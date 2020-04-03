from threading import Thread, Semaphore
from multiprocessing import cpu_count
import unittest, logging

# TODO
#
# Catch Exceptions
# Return Values
# Allow use of processes
# Tests if sequential and parallel return same values
# Remove print
# Clear comments
# Rename file to parallel.py
#

class Context(object):
	"""docstring for Context"""
	def __init__(self, args):
		super(Context, self).__init__()
		self.thread = None
		self.args  = args
		self.value = None
		self.exception = None

def parallel(iter_args, do=True, sem_value=cpu_count()):
	def wrap(func):
		def f():
			ctx = []
			sem = Semaphore(sem_value)
			def target(ctx):
				sem.acquire()
				try:
					ctx.value = func(*(ctx.args))
					pass
				except Exception as e:
					ctx.exception = exception
					pass
				sem.release()
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

def sequential(iter_args, do=True):
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

def test(SIZE, MAX_PARALLEL, mode):
	import numpy as np
	import pandas as pd
	import itertools
	import time
	# print('Alloc')
	data = np.random.randint(MAX_PARALLEL, size=SIZE)
	timestamp = np.cumsum(np.random.randint(1, 1000, size=SIZE))

	nxt = np.array(timestamp)
	idx = np.arange(len(nxt))
	unique = np.unique(data)

	iter_args = itertools.product(unique)

	start = time.time()
	# print('start')
	@mode(iter_args)
	def task(u):
		# These are numpy operations that release the python Global Interpreter Lock,
		# Ergo parallelism
		sel = data == u
		nxt[idx[sel][:-1]] = nxt[idx[sel][1:]]
	ctx = task()
	end = time.time()
	took = end-start
	# print('end')
	# print(f'took {took}')
	# if SIZE <= 100:
	# 	print(pd.DataFrame({
	# 		'data' : data,
	# 		'timestamp' : timestamp,
	# 		'nxt' : nxt,
	# 	}))
	return took

class TestParallel(unittest.TestCase):
	def test_filter(self):
		import itertools
		TESTS = itertools.product(
			[100000, 1000000, 10000000, 100000000],
			[2,10,100]
		)
		for SIZE, MAX_PARALLEL in TESTS:
			parallel_took   = test(SIZE, MAX_PARALLEL, parallel)
			sequential_took = test(SIZE, MAX_PARALLEL, sequential)
			diff = "%+2.f" % ((sequential_took-parallel_took)/sequential_took*100)
			logging.info(f'{diff}% ({SIZE},{MAX_PARALLEL})')
			# if parallel_took < sequential:
			# 	faster = 'parallel'
			# else:
			# 	faster = 'sequential'
			# print(f'{faster}({SIZE},{MAX_PARALLEL}) is faster')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
