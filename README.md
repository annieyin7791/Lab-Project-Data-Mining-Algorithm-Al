# Lab-Project-Data-Mining-Algorithm

**Project Goal**: Practice the use and implementation of data mining methods to discover the frequent itemset in
varied-scale synthetic datasets.

**Data Mining Algorithm Used**: Apriori & FP-Growth

**Steps**  
< Dataser Preparation>
1. Use a data generator to generate synthetic datasets (via C++). Link: https://github.com/zakimjz/IBMGenerator
2. Generate the following datasets for use later (Three configurations):
  A.Set number of transactions = 1,000, number of items = 600
  B. Set number of transactions = 100,000, number of items = 500
  C. Set number of transactions = 500,000, number of items = 500  
< Apriori Mining >
Mining the datasets generated in Step above using Apriori algorithm
1. Modify the source code from https://github.com/asaini/Apriori to print out the frequent itemset with support
2. Task 1: Mining all Frequent Itemset
3. Task 2: Mining all Frequent Closed Itemset

< FP-Growth Improvement>  
Conducting the mining task (only Task 1) in Step II using a non-Apriori algorithm with the goal to get performance (on efficiency) improvements as higher as possible.
