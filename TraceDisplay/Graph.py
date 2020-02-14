import py2neo
# from py2neo import Graph, Node, Relationship
import tracecmd
import logging
from Trace import event_to_dict

def load(path):
    per_pid = {}
    per_cpu = {}
    g = py2neo.Graph(host='neo4j')
    tx = g.begin()
    trace = tracecmd.Trace(path)
    for cpu in range(trace.cpus):
        logging.info('Reading events of cpu %d' % cpu)
        event = trace.read_event(cpu)
        while event:
            event = event_to_dict(event)
            pid = event['common_pid']
            node = py2neo.Node(event['event'], **event)
            per_cpu.setdefault(cpu,[]).append(node)
            per_pid.setdefault(pid,[]).append(node)
            event = trace.read_event(cpu)
    for cpu in per_cpu:
        for i in range(1, len(per_cpu[cpu])):
            prev = per_cpu[cpu][i-1]
            next = per_cpu[cpu][i]
            tx.create(py2neo.Relationship(prev,'per_cpu',next))
    for pid in per_pid:
        per_pid[pid] = sorted(per_pid[pid], key=lambda e:e['timestamp'])
        for i in range(1, len(per_pid[pid])):
            prev = per_pid[pid][i-1]
            next = per_pid[pid][i]
            tx.create(py2neo.Relationship(prev,'per_pid',next))
    tx.commit()
