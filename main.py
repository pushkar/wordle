import time
from itertools import product
from scipy.stats import entropy
import multiprocessing as mp

def load_words():
    allowed = []
    possible = []
    f = open("data/allowed_words.txt", "r")
    for l in f.readlines():
        allowed += [l.strip()]
    f = open("data/possible_words.txt", "r")
    for l in f.readlines():
        possible += [l.strip()]
    return allowed, possible

def filter_words(words, contains="", not_contains=""):
    if contains != "":
        words = list(filter(lambda x: all([c in x for c in contains]), words))
    if not_contains != "":
        words = list(filter(lambda x: not any([c in not_contains for c in x]), words))
    return words

def green(w, l, pos):
    return w[pos] == l

def yellow(w, l, pos):
    return not w[pos] == l and w.find(l) != -1

def gray(w, l, pos):
    return w.find(l) == -1

def entropy_for_word(query, allowed):
    counts = []
    for fns in product([green, yellow, gray], repeat=5):
        count = 0
        for word in allowed:
            if all(fns[i](word, query[i], i) for i in range(5)):
                count += 1
        counts += [count]

    probs = [float(count) / len(allowed) for count in counts]
    return entropy(probs, base=2)

def worker(word, allowed, q):
    ent = entropy_for_word(word, allowed)
    q.put(f"{word} {ent}")
    return f"{word} {ent}"

def listener(q):
    '''Listens for messages on the q, writes to file. '''
    with open("data/entropies.txt", 'w') as f:
        while 1:
            m = q.get()
            print(m)
            if m == 'kill':
                break
            f.write(str(m) + '\n')
            f.flush()

if __name__ == "__main__":
    allowed, possible = load_words()

    manager = mp.Manager()
    q = manager.Queue()    
    pool = mp.Pool(mp.cpu_count() + 2)
    watcher = pool.apply_async(listener, (q,))

    #fire off workers
    jobs = []
    for word in allowed:
        job = pool.apply_async(worker, (word, allowed, q))
        jobs.append(job)

    # collect results from the workers through the pool result queue
    for job in jobs: 
        job.get()

    q.put('kill')
    pool.close()
    pool.join()
