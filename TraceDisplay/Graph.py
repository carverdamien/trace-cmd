import logging

class Graph(object):
    def __init__(self, *args, **kwargs):
        # A node is ("NODE_TYPE", **labels)
        self._node = []
        # An egde is ("EDGE_TYPE", i, j, **labels) where i,j are indices in _node
        self._edge = []

    def load_trace(self, path):
        from Trace import event_to_dict
        import tracecmd
        node = []
        per_pid = {}
        per_cpu = {}
        trace = tracecmd.Trace(path)
        for cpu in range(trace.cpus):
            logging.info('Reading events of cpu %d' % cpu)
            event = trace.read_event(cpu)
            while event:
                event = event_to_dict(event)
                pid = event['common_pid']
                n = len(node)
                node.append((event['event'], event))
                per_cpu.setdefault(cpu,[]).append(n)
                per_pid.setdefault(pid,[]).append(n)
                event = trace.read_event(cpu)
        for pid in per_pid:
            logging.info('Sorting events per_pid[%d]' % pid)
            per_pid[pid] = sorted(per_pid[pid], key=lambda n:node[n][1]['timestamp'])
        chains = {
            'per_pid' : per_pid,
            'per_cpu' : per_cpu,
        }
        edge = [
            (k, chains[k][j][i-1], chains[k][j][i], {})
            for k in chains 
            for j in chains[k]
            for i in range(1,len(chains[k][j]))
        ]
        edge += build_additionnal_edges(node, per_pid)
        self._node = node
        self._edge = edge
        return

    def save(self, path):
        import pickle
        obj = {
            'node' : self._node,
            'edge' : self._edge,
        }
        with open(path, 'w') as f:
            logging.info('Saving %s' % path)
            pickle.dump(obj, f)

    def load(self, path):
        import pickle
        with open(path, 'r') as f:
            logging.info('Loading %s' % path)
            obj = pickle.load(f)
            self._node = obj['node']
            self._edge = obj['edge']

    def upload(self, uri, single=False, delete_all=False):
        import py2neo
        g = py2neo.Graph(uri)
        if delete_all:
            g.delete_all()
        if single:
            def begin(tx):
                return tx
            def commit(tx):
                pass
            def single_begin(tx):
                return g.begin()
            def single_commit(tx):
                tx.commit()
        else:
            def begin(tx):
                return g.begin()
            def commit(tx):
                tx.commit()
            def single_begin(tx):
                return tx
            def single_commit(tx):
                pass
        node = []
        tx = None
        tx = single_begin(tx)
        logging.info('Uploading nodes')
        for n in self._node:
            tx = begin(tx)
            node_type = n[0]
            node_properties = n[1]
            n = py2neo.Node(node_type, **node_properties)
            node.append(n)
            tx.create(n)
            commit(tx)
        logging.info('Uploading edges')
        for e in self._edge:
            tx = begin(tx)
            edge_start = node[e[1]]
            edge_type = e[0]
            edge_end = node[e[2]]
            edge_properties = e[3]
            edge = py2neo.Relationship(edge_start, edge_type, edge_end, **edge_properties)
            tx.create(edge)
            commit(tx)
        single_commit(tx)

def build_additionnal_edges(node, per_pid):
    import bisect
    # assert per_pid sorted by timestamp
    block = {
        # wakeup_target_pid : [ block_node_idx, ]
    }
    running = {
        # wakeup_target_pid : [ running_node_idx, ] # Array sorted by timestamp
    }
    wake_up = {
        # wakeup_target_pid : [ wakeup_node_idx, ] # Array sorted by timestamp
    }
    wake_up_new = {
        # wakeup_target_pid : wakeupnew_node_idx
    }
    def sched_switch(i):
        next_pid   = node[i][1]['next_pid']
        prev_pid   = node[i][1]['prev_pid']
        prev_state = node[i][1]['prev_state']
        if prev_state in ['S', 'D']: # INTERRUPTIBLE or UNINTERRUPTIBLE
            block.setdefault(prev_pid, []).append(i)
        # TODO:
        # elif prev_state in ['X', 'Z', 'I']: # EXIT_DEAD, EXIT_ZOMBIE, TASK_DEAD
        #     last_block[prev_pid] = i
        running.setdefault(next_pid, []).append(i)
        pass
    def sched_wakeup(i):
        pid = node[i][1]['pid']
        wake_up.setdefault(pid, []).append(i)
        pass
    def sched_wakeup_new(i):
        pid = node[i][1]['pid']
        if pid in wake_up_new:
            raise Exception()
        wake_up_new[pid] = i
        pass
    filtering = {
        'sched_switch'     : sched_switch,
        'sched_wakeup'     : sched_wakeup,
        'sched_wakeup_new' : sched_wakeup_new,
    }
    logging.info('Filtering')
    for pid in per_pid: 
        for i in per_pid[pid]:
            n = node[i]
            name = n[0]
            if name in filtering:
                filtering[name](i)
    sort = {
        'running': { 'data' : running, 'keys':{}},
        'wake_up': { 'data' : wake_up, 'keys':{}},
    }
    logging.info('Sorting')
    key = lambda n:node[n][1]['timestamp']
    for k,v in sort.items():
        for pid in v['data']:
            v['data'][pid] = sorted(v['data'][pid], key=key)
            v['keys'][pid] = [key(n) for n in v['data'][pid]]
    def find_next_unblock(pid, b):
        if pid not in sort['running']['keys']:
            return None
        i = bisect.bisect_right(sort['running']['keys'][pid], key(b))
        if i == len(sort['running']['data'][pid]):
            return None
        # assert key(b) != key(sort['running']['data'][pid][i])
        # assert key(b) < key(sort['running']['data'][pid][i])
        # assert i==0 or key(sort['running']['data'][pid][i-1]) < key(b)
        return sort['running']['data'][pid][i]
    def find_wake_up_between_block_and_unblock(pid, b, u):
        imin = bisect.bisect_right(sort['wake_up']['keys'][pid], key(b))
        imax = bisect.bisect_left(sort['wake_up']['keys'][pid], key(u))
        # assert imin==0 or key(sort['wake_up']['data'][pid][imin-1]) < key(b)
        # assert imax==len(sort['wake_up']['data'][pid]) or key(sort['wake_up']['data'][pid][imax]) > key(u)
        for i in range(imin, imax):
            # assert key(b) != key(sort['wake_up']['data'][pid][i])
            # assert key(b) < key(sort['wake_up']['data'][pid][i])
            # assert key(u) != key(sort['wake_up']['data'][pid][i])
            # assert key(u) > key(sort['wake_up']['data'][pid][i])
            yield sort['wake_up']['data'][pid][i]
    def find_block_unblock_edges():
        for pid in block:
            for b in block[pid]:
                u = find_next_unblock(pid, b)
                if not u:
                    logging.warn('Event not found: name==sched_switch, next_pid==%d' % pid)
                    continue
                for w in find_wake_up_between_block_and_unblock(pid, b, u):
                    yield ('block', b, w, {})
                    yield ('unblock', w, u, {})
    block_unblock_edges = list(find_block_unblock_edges())
    wake_up_new_edges = [
        ('wake_up_new', wake_up_new[pid], find_next_unblock(pid, wake_up_new[pid]), {})
        for pid in wake_up_new
    ]
    logging.debug(len(wake_up_new_edges))
    logging.debug(len(block_unblock_edges))
    return wake_up_new_edges + block_unblock_edges
