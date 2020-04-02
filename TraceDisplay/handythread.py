from threading import Thread, Semaphore
from multiprocessing import cpu_count

def parallel(iter_args, sem_value=cpu_count()):
	def wrap(func):
		def f():
			sem = Semaphore(sem_value)
			def target(*args):
				sem.acquire()
				func(*args)
				sem.release()
			def spawn(*args):
				t = Thread(target=target, args=args)
				t.start()
				return t
			threads = [spawn(*args) for args in iter_args]
			for t in threads:
				t.join()
		return f
	return wrap

def sequential(iter_args):
	def wrap(func):
		def f():
			for args in iter_args:
				func(*args)
		return f
	return wrap

def test(SIZE, MAX_PARALLEL, mode):
	# print('Alloc')
	data = np.random.randint(MAX_PARALLEL, size=SIZE)
	timestamp = np.cumsum(np.random.randint(1, 1000, size=SIZE))

	nxt = np.array(timestamp)
	idx = np.arange(len(nxt))
	unique = np.unique(data)

	iter_args = itertools.product(unique)

	@mode(iter_args)
	def task(u):
		# These are numpy operations that release the python Global Interpreter Lock,
		# Ergo parallelism
		sel = data == u
		nxt[idx[sel][:-1]] = nxt[idx[sel][1:]]
	start = time.time()
	# print('start')
	task()
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

if __name__ == '__main__':
	import numpy as np
	import pandas as pd
	import itertools
	import time
	TESTS = itertools.product(
		[100000, 1000000, 10000000, 100000000],
		[2,10,100]
	)
	for SIZE, MAX_PARALLEL in TESTS:
		parallel_took   = test(SIZE, MAX_PARALLEL, parallel)
		sequential_took = test(SIZE, MAX_PARALLEL, sequential)
		diff = "%+2.f" % ((sequential_took-parallel_took)/sequential_took*100)
		print(f'{diff}% ({SIZE},{MAX_PARALLEL})')
		# if parallel_took < sequential:
		# 	faster = 'parallel'
		# else:
		# 	faster = 'sequential'
		# print(f'{faster}({SIZE},{MAX_PARALLEL}) is faster')
