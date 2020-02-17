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
