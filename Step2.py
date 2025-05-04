import os
import argparse
from itertools import chain, combinations
from collections import defaultdict
import time
from memory_profiler import memory_usage
from tqdm import tqdm

def parse_args():
    parser = argparse.ArgumentParser(description="Run Apriori Algorithm")
    parser.add_argument("-f", "--inputFile", type=str, required=True, help="Dataset file path")
    parser.add_argument("-p", "--outputPath", type=str, required=True, help="Output file path")
    parser.add_argument("-s", "--minSupport", type=float, required=True, help="Minimum support value")
    return parser.parse_args()

def subsets(arr):
    """Returns non-empty subsets of arr"""
    return chain(*[combinations(arr, i + 1) for i, a in enumerate(arr)])

def returnItemsWithMinSupport(itemSet, transactionList, minSupport, freqSet):
    """Calculates the support for items in the itemSet and returns a subset
    of the itemSet each of whose elements satisfies the minimum support"""
    _itemSet = set()
    localSet = defaultdict(int)

    for item in tqdm(itemSet, desc="Processing itemsets for minSupport", total=len(itemSet)):
        for transaction in transactionList:
            if item.issubset(transaction):
                freqSet[item] += 1
                localSet[item] += 1

    for item, count in localSet.items():
        support = float(count) / len(transactionList)
        if support >= minSupport:
            _itemSet.add(item)

    return _itemSet

def joinSet(itemSet, length):
    joined_set = set([i.union(j) for i in itemSet for j in itemSet if len(i.union(j)) == length])
    return joined_set

def getItemSetTransactionList(data_iterator):
    transactionList = list()
    itemSet = set()
    for record in data_iterator:
        transaction = frozenset(record)
        transactionList.append(transaction)
        for item in transaction:
            itemSet.add(frozenset([item]))  
    return itemSet, transactionList

def runApriori(data_iter, minSupport):
    itemSet, transactionList = getItemSetTransactionList(data_iter)

    freqSet = defaultdict(int)
    largeSet = dict()
    candidates_stats = []

    oneCSet = returnItemsWithMinSupport(itemSet, transactionList, minSupport, freqSet)

    currentLSet = oneCSet
    k = 2
    while currentLSet != set([]):
        largeSet[k - 1] = currentLSet
        
        candidates_before = len(currentLSet)
        currentLSet = joinSet(currentLSet, k) 
        currentCSet = returnItemsWithMinSupport(currentLSet, transactionList, minSupport, freqSet)

        candidates_after = len(currentCSet)
        candidates_stats.append((k - 1, candidates_before, candidates_after))
        
        currentLSet = currentCSet
        k += 1

    toRetItems = []
    for key in largeSet:
        for item in largeSet[key]:
            support = float(freqSet[item]) / len(transactionList)
            toRetItems.append((item, support))
    
    return toRetItems, candidates_stats, freqSet

def findClosedItemsets(freqItems, freqSet):
    closedItemsets = []
    # itemsets_by_length
    itemsets_by_length = defaultdict(list)
    for item, support in freqItems:
        itemsets_by_length[len(item)].append((item, support))

    for item, support in freqItems:
        isClosed = True
        # Check if there is a superset with the same support
        larger_len = len(item) + 1
        if larger_len in itemsets_by_length:
            for otherItem, otherSupport in itemsets_by_length[larger_len]:
                if item.issubset(otherItem) and support == otherSupport:
                    isClosed = False
                    break

        if isClosed:
            closedItemsets.append((item, support))

    return closedItemsets

def write_closed_result_file(closedItems, dataset_name, min_support, output_path, total_time_task2, ratio):
    result_filename = f"{output_path}/step2_task2_{dataset_name}_{min_support}_closed_result.txt"
    with open(result_filename, 'w') as f:
        f.write(f"Total number of frequent closed itemsets: {len(closedItems)}\n")
        for item, support in sorted(closedItems, key=lambda x: x[1], reverse=True):
            itemset_str = "{" + ", ".join(item) + "}"
            f.write(f"{round(support * 100, 1)}%\t{itemset_str}\n")
        f.write(f"\nRatio of computation time compared to Task 1: {ratio:.2f}%\n")

    print(f"Closed itemset results written to {result_filename}")

def dataFromFile(fname):
    """Function which reads from the .data file and yields a generator"""
    with open(fname, "r") as file_iter:
        for line in file_iter:
            line = line.strip().split()  # Assuming the .data file uses space as a separator
            record = frozenset(line)  # Convert each line into a frozenset of items
            yield record

def runTask1(input_file, min_support, output_path, dataset_name):
    start_time_task1 = time.time()

    def task1_func():
        inFile = dataFromFile(input_file)
        items, candidates_stats, freqSet = runApriori(inFile, min_support)
        return items, candidates_stats, freqSet

    mem_usage_task1, (items, candidates_stats, freqSet) = memory_usage(task1_func, retval=True)

    if not items:
        print("Error: items is empty")
    if not freqSet:
        print("Error: freqSet is empty")

    end_time_task1 = time.time()
    total_time_task1 = end_time_task1 - start_time_task1
    print(f"Execution time for Task 1 (min_support {min_support}): {total_time_task1:.2f} seconds")
    print(f"Memory Usage for Task 1: {max(mem_usage_task1) - min(mem_usage_task1):.2f} MiB")
    
    write_result_files(items, candidates_stats, dataset_name, min_support, output_path, total_time_task1, mem_usage_task1)
    return items, freqSet, total_time_task1, mem_usage_task1

def write_result_files(items, candidates_stats, dataset_name, min_support, output_path, total_time_task1, mem_usage_task1):
    result_filename_1 = f"{output_path}/step2_task1_{dataset_name}_{min_support}_result.txt"
    with open(result_filename_1, 'w') as f:
        for item, support in sorted(items, key=lambda x: x[1], reverse=True):
            itemset_str = "{" + ", ".join(item) + "}"
            f.write(f"{round(support * 100, 1)}%\t{itemset_str}\n")
    print(f"Frequent itemset results written to {result_filename_1}")

    result_filename_2 = f"{output_path}/step2_task1_{dataset_name}_{min_support}_stats.txt"
    with open(result_filename_2, 'w') as f:
        f.write(f"Total number of frequent itemsets: {len(items)}\n")
        
        for k, before, after in candidates_stats:
            f.write(f"{k}\t{before}\t{after}\n")
        f.write(f"\nTotal execution time for Task 1: {total_time_task1:.2f} seconds\n")
        f.write(f"Memory Usage for Task 1: {max(mem_usage_task1) - min(mem_usage_task1):.2f} MiB\n")

    print(f"Frequent itemset statistics written to {result_filename_2}")

if __name__ == "__main__":
    args = parse_args()
    
    input_file = args.inputFile
    output_path = args.outputPath
    min_support = args.minSupport
    dataset_name = os.path.basename(input_file).split(".")[0]  

    print(f"Running Task 1 with min_support = {min_support}")

    items, freqSet, total_time_task1, mem_usage_task1 = runTask1(input_file, min_support, output_path, dataset_name)

    print(f"Running Task 2 with min_support = {min_support}")

    start_time_task2 = time.time()

    closedItemsets = findClosedItemsets(items, freqSet)

    end_time_task2 = time.time()
    total_time_task2 = end_time_task2 - start_time_task2
    print(f"Execution time for Task 2 (min_support {min_support}): {total_time_task2:.2f} seconds")
    ratio = (total_time_task2 / total_time_task1) * 100
    write_closed_result_file(closedItemsets, dataset_name, min_support, output_path, total_time_task2, ratio)
    print(f"Memory Usage for task1: {max(mem_usage_task1) - min(mem_usage_task1)} MiB")
