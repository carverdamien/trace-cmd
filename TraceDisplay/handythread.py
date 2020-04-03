from threading import Thread, Semaphore
from multiprocessing import cpu_count, Process, Queue
import unittest, logging

# TODO
#
# Allow use of processes
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

def parallel(iter_args, do=True, sem_value=cpu_count(), process=False):
	def wrap(func):
		def f():
			ctx = []
			sem = Semaphore(sem_value)
			def target(ctx):
				sem.acquire()
				if process:
					q = Queue()
					def target(q, *args):
						value = None
						exception = None
						try:
							value = func(*args)
						except Exception as e:
							exception = e
							pass
						q.put((value, exception))
					Process(target=target, args=(q,ctx.args)).start()
					value, exception = q.get()
					ctx.value     = value
					ctx.exception = exception
					pass
				else:
					try:
						ctx.value = func(*(ctx.args))
						pass
					except Exception as exception:
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

def parallel_process(iter_args, do=True, sem_value=cpu_count(), process=True):
	return parallel(iter_args, do, sem_value, process)

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

MODE = { k.__name__ : k for k in [sequential, parallel, parallel_process] }

class TestParallel(unittest.TestCase):
	def test_exception(self):
		def solve(n, mode, ctx):
			@mode(list(range(n)))
			def rez(i):
				if i == n/2:
					raise Exception(f'{i} == {n}/2')
			if ctx:
				return rez()
		N = 100
		for ctx in [True, False]:
			solve_return = [
				(mode_name, solve(N, mode, ctx))
				for mode_name, mode in MODE.items()
			]
			for j in range(len(solve_return)):
				if ctx:
					self.assertTrue(len(solve_return[0]),len(solve_return[j]))
					for i in range(len(solve_return[0])):
						self.assertEqual(solve_return[0][i].exception, solve_return[j][i].exception)
					self.assertEqual(solve_return[j][N/2].exception.message == f'{N/2} == {N}/2')
				else:
					self.assertTrue(solve_return[j] is None)
	def test_numpy(self):
		import itertools
		import numpy as np
		import time
		def timeit(func, args):
			start = time.time()
			value = func(*args)
			end   = time.time()
			return end-start, value
		def allocate(SIZE, MAX_PARALLEL):
			data = np.random.randint(MAX_PARALLEL, size=SIZE)
			timestamp = np.cumsum(np.random.randint(1, 1000, size=SIZE))
			nxt = np.array(timestamp)
			idx = np.arange(len(nxt))
			unique = np.unique(data)
			return (data, timestamp, idx, unique), nxt
		def solve(problem, solution, mode, ctx):
			data, timestamp, idx, unique = problem
			nxt = solution
			iter_args = itertools.product(unique)
			@mode(iter_args)
			def task(u):
				# These are numpy operations that release the python Global Interpreter Lock,
				# Ergo parallelism
				sel = data == u
				nxt[idx[sel][:-1]] = nxt[idx[sel][1:]]
				return np.sum(sel)
			if ctx:
				return task()
		TESTS = itertools.product(
			[100000, 1000000, 10000000, 100000000],
			[2,10,100],
			[True, False],
		)
		for SIZE, MAX_PARALLEL, CTX in TESTS:
			problem, solution = allocate(SIZE, MAX_PARALLEL)
			solution_sequential = solution
			solution_parallel   = solution.copy()
			self.assertFalse(solution_sequential is solution_parallel)
			sequential_took, sequential_value = timeit(solve, (problem, solution_sequential, sequential, CTX))
			parallel_took,   parallel_value   = timeit(solve, (problem, solution_parallel,   parallel  , CTX))
			self.assertTrue(np.array_equal(solution_sequential,solution_parallel))
			diff = "%+2.f" % ((sequential_took-parallel_took)/sequential_took*100)
			logging.info(f'{diff}% ({SIZE},{MAX_PARALLEL})')
			if CTX:
				self.assertTrue(len(sequential_value), len(parallel_value))
				for i in range(len(sequential_value)):
					self.assertEqual(sequential_value[i].value, parallel_value[i].value)
			else:
				self.assertTrue(sequential_value is None)
				self.assertTrue(parallel_value is None)
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
