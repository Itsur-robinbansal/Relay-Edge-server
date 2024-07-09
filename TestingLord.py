import sys

MAX_CPU_LIMIT = 100000
MAX_MEMORY_LIMIT = 3396000
MAX_DISK_LIMIT = 1996000

def Landlord(cache, C, ExecutableID_h, UsedCPUTime, UsedMemory, UsedLocalDiskSpace,cost_exe):
    print("passed values",ExecutableID_h, UsedCPUTime, UsedMemory, UsedLocalDiskSpace,cost_exe)
    eligible_for_eviction = []
    if ExecutableID_h not in cache:
        #print("Exe Not in cache", ExecutableID)
        #total_cpu_used = sum(cache[item]['CPU'] for item in cache)
        #total_memory_used = sum(cache[item]['Memory'] for item in cache)
        #total_disk_used = sum(cache[item]['Disk'] for item in cache)
        #print("total values:",total_cpu_used ,total_memory_used,total_disk_used )
        #print("MAx limits",MAX_CPU_LIMIT,MAX_MEMORY_LIMIT,MAX_DISK_LIMIT )
        eviction_complete = False
        delta = 0  # Initialize delta outside of the if block
        """
        if (
            total_cpu_used + UsedCPUTime > MAX_CPU_LIMIT or
            total_memory_used + UsedMemory > MAX_MEMORY_LIMIT or
            total_disk_used + UsedLocalDiskSpace > MAX_DISK_LIMIT
        ):
        """
        if(not enough_space(cache, UsedCPUTime, UsedMemory,UsedLocalDiskSpace)):
            cumulative_resources = {'CPU': 0, 'Memory': 0, 'Disk': 0}
            while True:
                if not cache:
                    print("Cache is empty. Cannot calculate delta.")
                    print("CACHE:Error:Cannot meet resource requirements") #Cannot meet the resource requirements even after emptying the cache
                    sys.exit()
                else:
                
                    print("cache",cache)
                    delta = min((cache[f]['credit'] / cache[f]['Disk']) for f in cache)
                    print("delta",delta,flush=True)
                    
                    # Create a list of files with the minimum delta value
                    min_list = [f for f in cache if (cache[f]['credit'] / cache[f]['Disk']) == delta]      #############newly added
                    print("min_list", min_list)
                    for f in cache:
                        print("credit and size for f",f,cache[f]['credit'],cache[f]['Disk'],flush=True)
                        cache[f]['credit'] -= delta * cache[f]['Disk']
                        print("new credit for exe",f,cache[f]['credit'],flush=True)
                        
                    for f in min_list:              ###########newly added
                        cache[f]['credit']=0       ########newly added
                        

                    eligible_for_eviction = [f for f in cache if cache[f]['credit'] == 0]
                    print("eligible_for_eviction:", eligible_for_eviction,flush=True)
                    evict_files = []
                    #cumulative_resources = {'CPU': 0, 'Memory': 0, 'Disk': 0}

                    # Calculate how much each eligible file contributes to meeting the requirements of the new file
                    file_contribution = {}
                    for file in eligible_for_eviction:
                        file_contribution[file] = {
                            'CPU': cache[file]['CPU'] - max(0, UsedCPUTime - cumulative_resources['CPU']),
                            'Memory': cache[file]['Memory'] - max(0, UsedMemory - cumulative_resources['Memory']),
                            'Disk': cache[file]['Disk'] - max(0, UsedLocalDiskSpace - cumulative_resources['Disk']),
                        }

                    # Sort the eligible files by their contribution to fulfilling the new file's requirements
                    sorted_eligible_files = sorted(eligible_for_eviction, key=lambda f: sum(file_contribution[f].values()))
                    #print("sorted_eligible_files:", sorted_eligible_files)

                    for file in sorted_eligible_files:
                        cumulative_resources['CPU'] += cache[file]['CPU']
                        cumulative_resources['Memory'] += cache[file]['Memory']
                        cumulative_resources['Disk'] += cache[file]['Disk']

                        evict_files.append(file)
                        #print("evict_files:", evict_files)
                        """
                        if (
                            cumulative_resources['CPU'] >= UsedCPUTime and
                            cumulative_resources['Memory'] >= UsedMemory and
                            cumulative_resources['Disk'] >= UsedLocalDiskSpace
                        ):
                            break  # Break if cumulative requirements are met
                        """
                        if (enough_space(cache, UsedCPUTime, UsedMemory,UsedLocalDiskSpace)):
                            break
                    if evict_files:  # Check if files are evicted
                        eviction_complete = True
                        for file_to_evict in evict_files:
                            if file_to_evict in cache:
                                evict_from_cache(cache, [file_to_evict])
                                #print("file_to_evict:", file_to_evict)
                        """
                        if (
                           cumulative_resources['CPU'] < UsedCPUTime or
                           cumulative_resources['Memory'] < UsedMemory or
                           cumulative_resources['Disk'] < UsedLocalDiskSpace
                        ):
                           #print("Conditions for eviction are still not met.")
                            # All eligible files have been evicted, but still not enough resources
                            # Clear the sorted_eligible_files list and recalculate credits for remaining items
                           sorted_eligible_files.clear()
                           #print("sorted_eligible_files:", sorted_eligible_files)
                           continue  # Repeat the eviction process for remaining files in cache 
                         """
                        if(not enough_space(cache, UsedCPUTime, UsedMemory,UsedLocalDiskSpace)):
                            # All eligible files have been evicted, but still not enough resources
                            # Clear the sorted_eligible_files list and recalculate credits for remaining items
                            sorted_eligible_files.clear()
                            continue
                    if eviction_complete:
                        bring_into_cache(cache, ExecutableID_h, UsedCPUTime, UsedMemory, UsedLocalDiskSpace, cost_exe)
                        return
                                         
        if len(cache) >= C:
           print("No of items exceeded")
           print("cache", cache)
           delta = min((cache[f]['credit'] / cache[f]['Disk']) for f in cache)
           print("delta", delta, flush=True)
           
           
           # Create a list of files with the minimum delta value
           min_list = [f for f in cache if (cache[f]['credit'] / cache[f]['Disk']) == delta]        #############newly added
           print("min_list", min_list)
           # Choose only one file for eviction
           #evict_file = None
           
           for f in cache:
               print("credit and size for f", f, cache[f]['credit'], cache[f]['Disk'], flush=True)
               cache[f]['credit'] -= delta * cache[f]['Disk']
               print("new credit for exe", f, cache[f]['credit'], flush=True)
           for f in min_list:                    ###########newly added
               cache[f]['credit']=0             ########newly added#
               evict_from_cache(cache, [f])
               print("file_to_evict:", f)
               bring_into_cache(cache, ExecutableID_h, UsedCPUTime, UsedMemory, UsedLocalDiskSpace, cost_exe)
               return
                     
               #if eviction_complete:
                        #bring_into_cache(cache, ExecutableID_h, UsedCPUTime, UsedMemory, UsedLocalDiskSpace, cost_exe)
                        #return
        else:
             bring_into_cache(cache, ExecutableID_h, UsedCPUTime, UsedMemory, UsedLocalDiskSpace, cost_exe)
    else:
        reset_credit(cache, ExecutableID_h,cost_exe)

def evict_from_cache(cache, evict_files):
    for file_to_evict in evict_files:
        if file_to_evict in cache:
            del cache[file_to_evict]
            print("FINAL CACHE",file_to_evict)
            #print("Updated cache after eviction:", cache)

def bring_into_cache(cache, ExecutableID_h, UsedCPUTime, UsedMemory, UsedLocalDiskSpace,cost_exe):
    print("cached values",ExecutableID_h, UsedCPUTime, UsedMemory, UsedLocalDiskSpace,cost_exe)
    cache[ExecutableID_h] = {
        'credit':cost_exe,
        'CPU': UsedCPUTime,
        'Memory': UsedMemory,
        'Disk': UsedLocalDiskSpace
        }
    
    for x in cache:
        print("FINAL CACHE",cache.keys(),flush=True)

def reset_credit(cache, ExecutableID_h,cost_exe):
   
    if ExecutableID_h in cache:
        cache[ExecutableID_h]['credit']=cost_exe
        #print("cost[ExecutableID]:", cost[ExecutableID])
    else:
        print ("ERROR")
   
def enough_space(cache, UsedCPUTime, UsedMemory,UsedLocalDiskSpace):
    total_cpu_used = sum(cache[item]['CPU'] for item in cache)
    total_memory_used = sum(cache[item]['Memory'] for item in cache)
    total_disk_used = sum(cache[item]['Disk'] for item in cache)
    if (
        total_cpu_used + UsedCPUTime > MAX_CPU_LIMIT or
        total_memory_used + UsedMemory > MAX_MEMORY_LIMIT or
        total_disk_used + UsedLocalDiskSpace > MAX_DISK_LIMIT
    ):
        return False
    else:
        return True
######################################################################################################################################################################################################

        

