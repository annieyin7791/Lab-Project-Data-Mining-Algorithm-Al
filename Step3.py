import time
import itertools
import argparse
from memory_profiler import memory_usage

class FPNode(object):
    __slots__ = ['value', 'count', 'parent', 'link', 'children']
    def __init__(self, value, count, parent):
        self.value = value
        self.count = count
        self.parent = parent
        self.link = None
        self.children = []

    def has_child(self, value):
        for node in self.children:
            if node.value == value:
                return True
        return False

    def get_child(self, value):
        for node in self.children:
            if node.value == value:
                return node
        return None

    def add_child(self, value):
        child = FPNode(value, 1, self)
        self.children.append(child)
        return child
    
    def remove_references(self):
        """Remove references to parent and link to free memory."""
        self.parent = None
        self.link = None

class FPTree(object):
    __slots__ = ['transactions', 'frequent', 'headers', 'root', 'tree_construction_time', 'tree_depth', 'node_count']

    def __init__(self, transactions, min_support, root_value=None, root_count=None, max_depth=None):
        start_time = time.time()
        transaction_count = len(transactions)
        self.frequent = self.find_frequent_items(transactions, min_support, transaction_count)
        self.headers = self.build_header_table(self.frequent)
        self.root = self.build_fptree(transactions, root_value, root_count, self.frequent, self.headers, max_depth)
        self.tree_construction_time = time.time() - start_time
        self.tree_depth = self.get_tree_depth(self.root)
        self.node_count = self.get_node_count(self.root)
        self.remove_unused_references(self.root)

    def find_frequent_items(self, transactions, min_support, transaction_count):
        items = {}
        for transaction in transactions:
            for item in transaction:
                if item in items:
                    items[item] += 1
                else:
                    items[item] = 1
        return {item: count for item, count in items.items() if count / transaction_count >= min_support}

    @staticmethod
    def build_header_table(frequent):
        headers = {}
        for key in frequent.keys():
            headers[key] = None
        return headers

    def build_fptree(self, transactions, root_value, root_count, frequent, headers, max_depth):
        root = FPNode(root_value, root_count, None)
        for transaction in transactions:
            sorted_items = [item for item in transaction if item in frequent]
            sorted_items.sort(key=lambda item: frequent[item], reverse=True)
            self.insert_tree(sorted_items, root, headers, max_depth)
        return root
    
    def insert_tree(self, items, node, headers, max_depth, depth=0):
        if max_depth is not None and depth >= max_depth:
            return
        if items:
            first, *rest = items
            child = node.get_child(first)
            if child:
                child.count += 1
            else:
                child = node.add_child(first)
                if headers[first] is None:
                    headers[first] = child
                else:
                    current = headers[first]
                    while current.link:
                        current = current.link
                    current.link = child
            self.insert_tree(rest, child, headers, max_depth, depth + 1)

    def get_tree_depth(self, node):
        if not node.children:
            return 1
        return 1 + max(self.get_tree_depth(child) for child in node.children)

    def get_node_count(self, node):
        count = 1
        for child in node.children:
            count += self.get_node_count(child)
        return count

    def remove_unused_references(self, node):
        """Recursively remove references to parent and link to free memory."""
        for child in node.children:
            self.remove_unused_references(child)
        node.parent = None
        node.link = None

    def tree_has_single_path(self, node):
        num_children = len(node.children)
        if num_children > 1:
            return False
        elif num_children == 0:
            return True
        else:
            return True and self.tree_has_single_path(node.children[0])

    def mine_patterns(self, min_support):
        if self.tree_has_single_path(self.root):
            return self.generate_pattern_list()
        else:
            return self.zip_patterns(self.mine_sub_trees(min_support))

    def zip_patterns(self, patterns):
        suffix = self.root.value
        if suffix is not None:
            new_patterns = {}
            for key in patterns.keys():
                new_patterns[tuple(sorted(list(key) + [suffix]))] = patterns[key]
            return new_patterns
        return patterns

    def generate_pattern_list(self):
        patterns = {}
        items = self.frequent.keys()
        if self.root.value is None:
            suffix_value = []
        else:
            suffix_value = [self.root.value]
            patterns[tuple(suffix_value)] = self.root.count
        for i in range(1, len(items) + 1):
            for subset in itertools.combinations(items, i):
                pattern = tuple(sorted(list(subset) + suffix_value))
                patterns[pattern] = min([self.frequent[x] for x in subset])
        return patterns

    def mine_sub_trees(self, min_support):
        patterns = {}
        seen_patterns = set()  # 記錄已經計算的模式
        mining_order = sorted(self.frequent.keys(), key=lambda x: self.frequent[x])

        for item in mining_order:
            suffixes = []
            conditional_tree_input = []
            node = self.headers[item]

            while node is not None:
                suffixes.append(node)
                node = node.link

            for suffix in suffixes:
                frequency = suffix.count
                path = []
                parent = suffix.parent

                while parent is not None and parent.parent is not None:
                    path.append(parent.value)
                    parent = parent.parent

                for i in range(frequency):
                    conditional_tree_input.append(path)

            subtree = FPTree(conditional_tree_input, min_support, item, self.frequent[item])
            subtree_patterns = subtree.mine_patterns(min_support)

            for pattern in subtree_patterns.keys():
                if pattern in seen_patterns:
                    continue  # Skip already calculated patterns
                seen_patterns.add(pattern)

                if pattern in patterns:
                    patterns[pattern] += subtree_patterns[pattern]
                else:
                    patterns[pattern] = subtree_patterns[pattern]
        return patterns

def find_frequent_patterns(transactions, min_support, max_depth=None):
    tree = FPTree(transactions, min_support, None, None, max_depth)
    return tree.mine_patterns(min_support), tree

def generate_patterns_rules(data, support, max_depth=None):
    transactions = open_data(data)
    pattern, tree = find_frequent_patterns(transactions, support, max_depth)
    transaction_count = len(transactions)
    return pattern, tree, transaction_count

def open_data(file):
    transactions = []
    with open(file, 'r') as database:
        for line in database:
            transactions.append(line.strip().split())
    return transactions

def write_result_file(patterns, output_path, dataset_name, min_support, transaction_count):
    result_filename = f"{output_path}/step3_task1_{dataset_name}_{min_support}_results.txt"
    with open(result_filename, 'w') as f:
        for pattern, support in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
            if support >= min_support:
                itemset_str = "{" + ", ".join(str(item) for item in pattern) + "}"
                support_percentage = round((support / transaction_count) * 100, 1)
                f.write(f"{support_percentage}%\t{itemset_str}\n")
    print(f"Frequent itemset results written to {result_filename}")

def write_statistics_file(tree, total_itemsets, output_path, total_execution_time, dataset_name, min_support, mem_usage):
    stat_filename = f"{output_path}/step3_task1_{dataset_name}_{min_support}_stats.txt"
    with open(stat_filename, 'w') as f:
        f.write(f"Total number of frequent itemsets: {total_itemsets}\n")
        f.write(f"FP-Tree Depth: {tree.tree_depth}\n")
        f.write(f"FP-Tree Node Count: {tree.node_count}\n")
        f.write(f"Tree Construction Time: {tree.tree_construction_time:.2f} seconds\n")
        f.write(f"Total execution time: {total_execution_time:.2f} seconds\n")
        f.write(f"Memory Usage: {max(mem_usage) - min(mem_usage)} MiB\n")
        f.write(f"1\tN/A\t{total_itemsets}\n")
    print(f"Statistics written to {stat_filename}")

def run_and_monitor():
    def run_fpgrowth():
        patterns, tree, transaction_count = generate_patterns_rules(input_file, min_support, max_depth)
        total_itemsets = len(patterns)
        write_result_file(patterns, output_path, dataset_name, min_support, transaction_count)
        return patterns, tree, total_itemsets

    mem_usage, (patterns, tree, total_itemsets) = memory_usage(
        (run_fpgrowth, ()), retval=True
    )

    return patterns, tree, total_itemsets, mem_usage

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run FP-Growth Algorithm")
    parser.add_argument("-f", "--inputFile", type=str, required=True, help="Dataset file path")
    parser.add_argument("-s", "--minSupport", type=float, required=True, help="Minimum support value")
    parser.add_argument("-p", "--outputPath", type=str, required=True, help="Output file path")
    parser.add_argument("-d", "--maxDepth", type=int, required=False, help="Maximum tree depth", default=None)
    
    args = parser.parse_args()
    input_file = args.inputFile
    min_support = args.minSupport
    output_path = args.outputPath
    max_depth = args.maxDepth
    dataset_name = input_file.split("/")[-1].split(".")[0]

    start_time = time.time()
    patterns, tree, total_itemsets, mem_usage = run_and_monitor()

    total_execution_time = time.time() - start_time

    write_statistics_file(
        tree,
        total_itemsets,
        output_path,
        total_execution_time,
        dataset_name,
        min_support,
        mem_usage,
    )
    print(f"Total execution time: {total_execution_time:.2f} seconds")
    print(f"Memory Usage: {max(mem_usage) - min(mem_usage)} MiB")