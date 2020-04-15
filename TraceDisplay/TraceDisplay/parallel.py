from multiprocessing import cpu_count
import logging

# TODO
#
# use parallel_process in test_numpy
#

class Context(object):
	"""docstring for Context"""
	def __init__(self, args):
		super(Context, self).__init__()
		self.thread = None
		self.args  = args
		self.value = None
		self.exception = None

def parallel_thread(iter_args, do=True, sem_value=cpu_count()):
	from threading import Thread, Semaphore
	def wrap(func):
		def f():
			ctx = []
			sem = Semaphore(sem_value)
			def target(ctx):
				sem.acquire()
				try:
					ctx.value = func(*(ctx.args))
					pass
				except Exception as exception:
					ctx.exception = exception
					pass
				sem.release()
				return
			logging.debug('Spawning threads')
			for args in iter_args:
				c = Context(args)
				c.thread = Thread(target=target, args=(c,))
				c.thread.start()
				ctx.append(c)
			logging.debug('Joining threads')
			for c in ctx:
				c.thread.join()
			return ctx
		if do:
			ctx = f()
			return lambda : ctx
		return f
	return wrap

def parallel_process(iter_args, do=True, sem_value=cpu_count()):
	from multiprocessing import Process, Queue, Semaphore
	def wrap(func):
		def f():
			ctx = []
			process = []
			sem = Semaphore(sem_value)
			q = Queue()
			def target(i,q,args):
				value = None
				exception = None
				sem.acquire()
				try:
					value = func(*args)
					pass
				except Exception as e:
					exception = e
					pass
				q.put((i,value,exception))
				sem.release()
				return
			logging.debug('Spawning processes')
			i = 0
			for args in iter_args:
				c = Context(args)
				ctx.append(c)
				p = Process(target=target, args=(i,q,args))
				p.start()
				process.append(p)
				i+=1
			logging.debug('Pulling')
			for _ in range(len(process)):
				i, value, exception = q.get()
				ctx[i].value = value
				ctx[i].exception = exception
			logging.debug('Joining processes')
			for p in process:
				p.join()
			return ctx
		if do:
			ctx = f()
			return lambda : ctx
		return f
	return wrap

def sequential(iter_args, do=True, sem_value=None):
	def wrap(func):
		def f():
			ctx = []
			def target(ctx):
				try:
					ctx.value = func(*(ctx.args))
					pass
				except Exception as exception:
					ctx.exception = exception
					pass
			logging.debug('Start sequential')
			for args in iter_args:
				c = Context(args)
				target(c)
				ctx.append(c)
			logging.debug('End sequential')
			return ctx
		if do:
			ctx = f()
			return lambda : ctx
		return f
	return wrap

# Default parallel is thread
def parallel(iter_args, do=True, sem_value=cpu_count()):
	return parallel_thread(iter_args, do, sem_value)

MODE = { k.__name__ : k for k in [sequential, parallel_thread, parallel_process] }
