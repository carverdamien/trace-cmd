from TraceDisplay import parallel, parallel_process, parallel_thread, sequential, MODE
import unittest, logging

class TestParallel(unittest.TestCase):
	def test_exception(self):
		import itertools
		def solve(n, mode, ctx):
			iter_args = itertools.product(list(range(n)))
			@mode(iter_args)
			def rez(i):
				if i == n/2:
					raise Exception(f'{i} == {n}/2')
				return i*2
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
					self.assertTrue(len(solve_return[0][1]),len(solve_return[j][1]))
					for i in range(len(solve_return[0][1])):
						self.assertEqual(str(solve_return[0][1][i].exception), str(solve_return[j][1][i].exception))
						self.assertEqual(solve_return[0][1][i].value, solve_return[j][1][i].value)
						if solve_return[j][1][i].value is not None:
							self.assertEqual(solve_return[j][1][i].value, i*2)
					self.assertEqual(str(solve_return[j][1][N//2].exception), f'{N//2} == {N}/2')
				else:
					self.assertTrue(solve_return[j][1] is None)
	def test_pandas(self):
		import itertools
		import pandas as pd
		import time, random
		def timeit(func, args):
			start = time.time()
			value = func(*args)
			end   = time.time()
			return end-start, value
		def allocate(SIZE, MAX_PARALLEL, NR_CPU):
			cpu = {i:{} for i in range(NR_CPU)}
			cpus = list(cpu.keys())
			for s in range(SIZE):
				e = random.randint(0, MAX_PARALLEL)
				i = random.choice(cpus)
				cpu[i].setdefault(e,[]).append({
					'timestamp':s,
					'var':random.randint(0,100),
				})
			problem = cpu, SIZE, MAX_PARALLEL, NR_CPU
			return problem
		def solve(problem, mode):
			cpu, SIZE, MAX_PARALLEL, NR_CPU = problem
			@mode(itertools.product(range(MAX_PARALLEL)))
			def foreach(e):
				df = pd.concat([
					pd.DataFrame(cpu[i][e])
					for i in cpu
					if e in cpu[i]
				])
				df.set_index(
					'timestamp',
					verify_integrity=True,
					inplace=True,
				)
				df.sort_index(
					ascending=True,
					inplace=True,
				)
				return e, df
			return foreach()
		TESTS = itertools.product(
			[100000, 1000000, 10000000],
			[10, 100],
			[10, 100],
		)
		for SIZE, MAX_PARALLEL, NR_CPU in TESTS:
			logging.info(f'{SIZE} {MAX_PARALLEL} {NR_CPU}')
			problem = allocate(SIZE, MAX_PARALLEL, NR_CPU)
			result = {}
			for mode_name, mode in MODE.items():
				result[mode_name] = timeit(solve, (problem, mode))
			for mode_name, r in result.items():
				took, ctx = r
				logging.info(f'{mode_name} took {took}')
			it = iter(list(result.items()))
			base_k, base_v = next(it)
			base_took, base_ctx = base_v
			base_solution = {
				ctx.value[0] : ctx.value[1]
				for ctx in base_ctx
			}
			for k,v in it:
				k_took, k_ctx = v
				for ctx in k_ctx:
					# print(ctx.value[1].head())
					# print(base_solution[ctx.value[0]].head())
					self.assertTrue(ctx.value[1].equals(base_solution[ctx.value[0]]))
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
