import csv
import sys
import statistics
import numpy as np
import os
import threading
import time
from TestingLord import Landlord

##########################################


data_rate_li = 30  # in Mbps Uplink bandwidth
data_rate_Mi = 40  # in Mbps ###Downlink bandwidth
speedtime = 5 # Ratio of distance b/w cloud and edge to distance b/w edge to next edge
mod = 2 # number of edges
C = 70 # maximum cache size

SIZEFACTOR = 1073741824 #2^30
# SIZEFACTOR = 10000000 #10^7

orig_stdout = sys.stdout
f = open(os.devnull, 'w')
sys.stdout = f


# Initialize an empty list of list to store ExecutableID values
priv_q = [[] for _ in range(mod)]
# Initialize an empty list to store Timestamp values
SubmitTime_list = [[] for _ in range(mod)]
#Invalid rows
skipped_rows = [[] for _ in range(mod)]
#To store the first miss in the horizon or first miss after eviction
miss_time_dict=[{} for _ in range(mod)] #Key: ExecutableID, Values: [status or timestamp]
#To store the resources associated with each executable
resources_dict= [{} for _ in range(mod)]
# Initialize an empty list to store UsedLocalDiskSpace values
Mi_bytes = [[] for _ in range(mod)]
# Initialize an empty dictionary  of list to store time to cloud 
time_for_executables = [{} for _ in range(mod)]
# Initialize an empty dictionary  of list to store time to edge 
time_for_executabletoedge = [{} for _ in range(mod)]
# Initialize an empty list of list to store downloading cost
time_seconds_Mi =  [[] for _ in range(mod)]
# Initialize the private 'cache' dictionary
priv_cache = [{} for _ in range(mod)]
# Initialize the dictionary to save which edge it is forwarded
forwarded_to_edge = [{} for _ in range(mod)]




#initilize every same variable for public fles
pub_q = [[] for _ in range(mod)]
pubq_edge_in_data = [[] for _ in range(mod)]
pubq_index_in_data = [[] for _ in range(mod)]
pubq_SubmitTime_list = [[] for _ in range(mod)]
pubq_time_seconds_Mi =  [[] for _ in range(mod)]
pubq_miss_time_dict = [{} for _ in range(mod)]
pubq_Mi_bytes = [[] for _ in range(mod)]
pubq_resources_dict= [{} for _ in range(mod)]
pubq_time_for_executables = [{} for _ in range(mod)]
pubq_time_for_executabletoedge = [{} for _ in range(mod)]
pub_cache = [{} for _ in range(mod)]

# Initialize a counter for each edge
skipped_counter = [0] * mod
max_requests = [0]  * mod
data_size = [0]  * mod



##########################################################################################



for i in range(0, mod):
    fname = f"Google{i+1}-median.csv"
    # fname = f"1.1.6-delayed.csv"
    
    with open(fname, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')  # Use ',' as the delimiter
        max_requests[i] = 0
        # next(csv_reader)  # Skip the header line if it exists

        for row_index, line_dataset in enumerate(csv_reader):
            has_zero = False
            for index, value in enumerate(line_dataset):
                if index in [2, 3, 4] and float(value) == 0:  # Checking columns 2, 3, and 4 for zero values
                   has_zero = True
                   skipped_rows[i].append(line_dataset)# Save the entire row to the list
                   skipped_counter[i] += 1
                   break

            if has_zero:
               continue  # Skip this row if it contains a zero value
            max_requests[i] +=1
        
            if len(line_dataset) >= 5:
            # Extract values from line_dataset
                ExecutableID = f"{line_dataset[0]}"#line_dataset[0]
                SubmitTime = line_dataset[1]
                UsedCPUTime = float(line_dataset[2])
                UsedMemory = float(line_dataset[3])
                UsedLocalDiskSpace = float(line_dataset[4])
                Mi_bytes[i].append(UsedLocalDiskSpace)
                priv_q[i].append(ExecutableID)
                SubmitTime_list[i].append(SubmitTime)
                miss_time_dict[i][ExecutableID] = -1
                resources_dict[i][ExecutableID] = [UsedCPUTime,UsedMemory,UsedLocalDiskSpace]
            
                   
    #Find the median service size, divide by 10 and scale to get the size of a request              
    data_size[i] = (statistics.median(Mi_bytes[i])*1/10)*SIZEFACTOR
      

class DownloadSession:
    def __init__(self):
        self.dldbegin = False
        
# Create an instance of DownloadSession
ExecutableID = DownloadSession()



#####################################################################################



def calculate_time_li(li_bytes, data_rate_li, data_rate_Mi):
    time_seconds = (li_bytes / data_rate_li)+(li_bytes /data_rate_Mi )
    return time_seconds

time_second =  [0] * mod
for i in range(0, mod):
    time_second[i] = calculate_time_li( data_size[i], data_rate_li,data_rate_Mi)

# Define a function to calculate forwarding time for a specific ExecutableID
def calculate_time_for_executable(ExecutableID, li_bytes, data_rate_li, data_rate_Mi):
    time_seconds = calculate_time_li(li_bytes, data_rate_li,data_rate_Mi)
    return time_seconds

# Calculate forwarding time for each ExecutableID and store it in a dictionary
for i in range(0, mod):
    for ExecutableID in priv_q[i]:
        time_seconds = calculate_time_for_executable(ExecutableID, data_size[i], data_rate_li,data_rate_Mi)
        time_for_executables[i][ExecutableID] = time_seconds
# Now, we have a dictionary 'time_for_executables' that contains the forwarding time for each ExecutableID


# Now, dictionary 'time_for_executabletoedge' that contains the forwarding time to next edge 
time_for_executabletoedge = [{k: v / speedtime for k, v in d.items()} for d in time_for_executables]



######################################################################################



## time_seconds_Mi is the downloading time
def calculate_time_Mi(Mi_bytes, data_rate_Mi, i):
    time_seconds_Mi = [value*1073741824/ data_rate_Mi + time_second[i] for value in Mi_bytes]##*1048576
    return time_seconds_Mi

#time_second_Mi store time to download each executable for each edge
for i in range(0, mod):
    time_seconds_Mi[i] = calculate_time_Mi(Mi_bytes[i], data_rate_Mi, i)


########################################################################################


# Initialize the 'cloud' dictionary
cloud = {}

# Initialize the 'buffer' dictionary
buffer = {}



##########################################################################################


#Ti = time until the current request from the earliest cache miss after which there is no cache hit.
#Li = sum of the forwarding times until the current request from the earliest cache miss after which there is no cache hit.


def GETPENALTY(ExecutableID, SubmitTime,  flag, edge, queue):
    
    #CHeck for list is public or private
    if flag == 'priv':
        if (miss_time_dict[edge][ExecutableID] >= 0):
            Ti = float(SubmitTime) - miss_time_dict[edge][ExecutableID]
            Li = 0
      
            for i, submit_time_str in enumerate(SubmitTime_list[edge],start=0):
              
                temp_submit_time = float(submit_time_str) # Convert the string to an integer
               
                if (temp_submit_time < miss_time_dict[edge][ExecutableID]):
                    continue #Measure only from the latest cache miss
                if i >= len(queue):
                    break  # Stop the loop if we've processed all available ExecutableIDs

            # Check if the current request's ExecutableID matches the one we're calculating for
                if ExecutableID == queue[i]:
                    Li += time_for_executabletoedge[edge][ExecutableID] #Add the time until the current request
                
                if temp_submit_time == float(SubmitTime):
                    break #NEW
                
    else:
        
        if (pubq_miss_time_dict[edge][ExecutableID] >= 0):
            Ti = float(SubmitTime) - pubq_miss_time_dict[edge][ExecutableID]
            Li = 0
            
            for i, submit_time_str in enumerate(pubq_SubmitTime_list[edge],start=0):
                temp_submit_time = float(submit_time_str)  # Convert the string to an integer

                if (temp_submit_time < pubq_miss_time_dict[edge][ExecutableID]):
                    continue #Measure only from the latest cache miss
                if i >= len(queue):
                    break  # Stop the loop if we've processed all available ExecutableIDs

            # Check if the current request's ExecutableID matches the one we're calculating for
                if ExecutableID == queue[i]:
                    Li += pubq_time_for_executables[edge][ExecutableID]  #Add the time until the current request
                
                if temp_submit_time == float(SubmitTime):
                    break #NEWxxxxxxxxxxxxxxxxxxxxxv
                
   
            Li+= pubq_time_for_executabletoedge[edge][ExecutableID]  
                             
    return Ti, Li



######################################################################################



def PREPARETOCACHE(cache,ExecutableID, edge,queue,flag):
    
    #The credit for an item is the download time Mi
    if flag == 'priv':
        exec_cost_local = time_seconds_Mi[edge][queue.index(ExecutableID)]
        resources_d = resources_dict[edge]
        
    elif flag == 'pub':
        exec_cost_local = pubq_time_seconds_Mi[edge][queue.index(ExecutableID)]
        resources_d = pubq_resources_dict[edge]
        

    # exec_cost_local = Glob[ExecutableID_list.index(ExecutableID)]
    LLCA(cache, exec_cost_local, ExecutableID, resources_d)
    
    
    
########################################################################



#function to sent forward request to the desired edges and filling the values
def Hash(Executable, row_counter,edge):

    # Convert Executable to an integer for further calculations
    ExecutableID = int(Executable)
    
    # Determine the list based on the remainder
    remainder = ExecutableID % mod
    
    # Append the appropriate public queue based on the remainder
    forwarded_to_edge[edge][Executable] = remainder
    pub_q[remainder].append(Executable)
    pubq_edge_in_data[remainder].append(edge)
    pubq_index_in_data[remainder].append(row_counter)
    pubq_SubmitTime_list[remainder].append(SubmitTime_list[edge][row_counter])
    pubq_time_seconds_Mi[remainder].append(time_seconds_Mi[edge][row_counter])
    pubq_Mi_bytes[remainder].append(Mi_bytes[edge][row_counter])
    pubq_miss_time_dict[remainder][Executable]  = -1
    pubq_time_for_executables[remainder][Executable] =  time_for_executables[edge][Executable]
    pubq_time_for_executabletoedge[remainder][Executable] = time_for_executabletoedge[edge][Executable]
    pubq_resources_dict[remainder][Executable] = resources_dict[edge][Executable]
    
    return len(pub_q[remainder])

    
##############################################################################

          
    
def HANDLE_SERVICE_REQUEST(edge, queue, flag, cache, name):

    # Initialize dictionaries and lists as required
    pending_downloads = []
    
    # Initialize a list to store the remaining times for this ExecutableID
    dld_start_time_dict = {}
    
    # Initialize a list to store cache hits
    cache_hits = []
    
    # Initialize a counter variable
    buffer_counter = 0
    forward_counter = 0 
    cost_counter =0 ### added
    
    #counts which we are working on
    row_number = 0 
    
    #takes desired name we provide in parameters
    file_name = f'{name}.txt'
   
    # Open a file in write mode ('w')
    with open(file_name, 'w') as file:
        
        # Initialize total latency
        total_latency = 0
        
        # wait time for let few values be in public queue
        if flag == 'pub':
            time.sleep(1)
            
        #Submit Time of 1st Executableid
        if flag == 'priv':
            SubmitTime  = SubmitTime_list[edge][0]
        
        elif flag == 'pub':
            SubmitTime  = pubq_SubmitTime_list[edge][0]   
            
        #running for each id in queue  
        for ExecutableID in queue:
            
            # Move the initialization inside the loop to reset the variables for each ExecutableID
            latency_cloud = ""
            latency_buffer = ""
            latency_cache = ""
            latency_edge = ""
            latency_edge_row = ""
            remaining_time = 0.0 
            exec_cost = 0.0
            exec_cost_cache = 0.0
            
            ##Moved up from the end. 
            row = 0
            idxs_toremove=[]
            for temp_exe in pending_downloads:
                
                #If download was initiated for this request, it is not yet time to cache
                if flag == 'priv':
                     if (( (dld_start_time_dict[temp_exe]+ float(time_seconds_Mi[edge][queue.index(temp_exe)]) - float(SubmitTime)) <= 0.0 )  ):
                     
                   #Cache the service. For caching, the existing Ti and Li values must be used.

                        PREPARETOCACHE(cache,temp_exe, edge , queue, flag )
                        #From now on, Ti and Li will be 0 until the next cache muss
                        miss_time_dict[edge][temp_exe] = -1
                        idxs_toremove.append(row)
                        
                elif flag == 'pub':
                     if (( (dld_start_time_dict[temp_exe]+ float(pubq_time_seconds_Mi[edge][queue.index(temp_exe)]) - float(SubmitTime)) <= 0.0)):
                           PREPARETOCACHE(cache,temp_exe, edge, queue, flag)
                           pubq_miss_time_dict[edge][temp_exe] = -1
                           idxs_toremove.append(row)   
                     
                row+=1   
                         
            #Remove the indices marked for removal
            temp_arr = np.array(pending_downloads)
            temp_arr = np.delete(temp_arr,idxs_toremove)
            pending_downloads = temp_arr.tolist()
            ###Moved up from the end
            
            if ExecutableID in cache:
               # cache hit 
               # Add the ExecutableID to the cache_hits list
               cache_hits.append(ExecutableID)
               dld_start_time_dict.pop(ExecutableID,None)
               
            else:
                #Cache miss for ExecutableId in qqueue
 
                #Calculate Ti, Li   
                if flag == 'priv':
                    if (miss_time_dict[edge][ExecutableID] == -1):
                        miss_time_dict[edge][ExecutableID] = float(SubmitTime)
                        
                    Ti, Li = GETPENALTY(ExecutableID, SubmitTime,'priv', edge , queue)
                    
                    
                elif flag == 'pub':
                    if (pubq_miss_time_dict[edge][ExecutableID] == -1):
                        pubq_miss_time_dict[edge][ExecutableID] = float(SubmitTime)
                        
                    Ti, Li = GETPENALTY(ExecutableID, SubmitTime, 'pub', edge , queue)
                
                
                # calculate cost for the given edge
                if flag == 'priv':
                    exec_cost = time_seconds_Mi[edge][queue.index(ExecutableID)]
                
                elif flag == 'pub':
                    exec_cost = pubq_time_seconds_Mi[edge][queue.index(ExecutableID)]
                    
                
                
                if (Ti >= exec_cost or Li >= exec_cost) and ExecutableID not in pending_downloads: #Initiate download
                    pending_downloads.append(ExecutableID)
                    
                    #downloading put value in cloud
                    if flag == "pub":
                        cloud[ExecutableID] = ExecutableID
                    
                    if flag == 'pub':
                       latency_cloud = f"Latency to cloud for ExecutableID {ExecutableID}: {pubq_time_for_executables[edge][ExecutableID]}"
                       
                    elif flag == 'priv':
                         latency_cloud = f"Latency to next edge for ExecutableID {ExecutableID}: {time_for_executabletoedge[edge][ExecutableID]}"

                    # calculate which edge to forward
                    if flag == 'priv':
                        index = Hash(ExecutableID, row_number,edge)
                        latency_edge = f"Forwarded to public edge {forwarded_to_edge[edge][ExecutableID] + 1}"
                        latency_edge_row = f"Row Number: {index}"
                    
                    #Increment the counter
                    forward_counter += 1
                       
                    # Calculate cost if download is initiated
                    if flag == 'priv':
                        exec_cost_cache = time_seconds_Mi[edge][queue.index(ExecutableID)]
                
                    elif flag == 'pub':
                        exec_cost_cache = pubq_time_seconds_Mi[edge][queue.index(ExecutableID)]
                                        
                    cost_counter += exec_cost_cache  ####
                    
                     #Start of download time for this executable
                    dld_start_time_dict[ExecutableID] = float(SubmitTime)
                    
                    
                    #not download_status.get(ExecutableID, False): #Forward to cloud 
                elif (Ti < exec_cost or Li < exec_cost) and (ExecutableID not in pending_downloads):
                   
                    #downloading put value in cloud
                    if flag == "pub":
                        cloud[ExecutableID] = ExecutableID
                        
                    if flag == 'pub':
                        latency_cloud = f"Latency to cloud for ExecutableID {ExecutableID}: {pubq_time_for_executables[edge][ExecutableID]}"
                       
                    elif flag == 'priv':
                        latency_cloud = f"Latency to next edge for ExecutableID {ExecutableID}: {time_for_executabletoedge[edge][ExecutableID]}"
                     
                    # calculate which edge to forward    
                    if flag == 'priv':
                        index = Hash(ExecutableID, row_number,edge)
                        latency_edge = f"Forwarded to public edge {forwarded_to_edge[edge][ExecutableID] + 1}"
                        latency_edge_row = f"Row Number: {index}"
                        
                    #Increment the counter
                    forward_counter += 1
   
                          
                else: #Is being downloaded, check the remaining time. Forward or buffer
                    
                    if ExecutableID in pending_downloads:
                       
                        #remaining time
                        remaining_time = dld_start_time_dict[ExecutableID]+exec_cost - float(SubmitTime)
                       
                        #time to forward                 
                        if flag =='pub':
                            time_to_fwd = pubq_time_for_executables[edge][ExecutableID]                       
                        elif flag == 'priv':
                            time_to_fwd = time_for_executabletoedge[edge][ExecutableID]                       
                       
                        # Check conditions and take actions
                        if remaining_time > time_to_fwd:  # time_seconds is forwarding time
                            
                          
                            if flag == 'pub':
                                cloud[ExecutableID] = ExecutableID
                                latency_cloud = f"Latency to cloud for ExecutableID {ExecutableID}: {pubq_time_for_executables[edge][ExecutableID]}" 
                                                   
                            elif flag == 'priv':
                                latency_cloud = f"Latency to next edge for ExecutableID {ExecutableID}: {time_for_executabletoedge[edge][ExecutableID]}" 
                          
                            # calculate which edge to forward
                            if flag == 'priv':
                                index = Hash(ExecutableID, row_number,edge)
                                latency_edge = f"Forwarded to public edge {forwarded_to_edge[edge][ExecutableID] + 1}"
                                latency_edge_row = f"Row Number: {index}"
 
                            latency_buffer = ""  # Set buffer latency to blank
                            
                            # Increment the counter
                            forward_counter += 1
                                      
                        if 0 < remaining_time <= time_to_fwd:  # Ensure remaining_time is greater than 0 and less than or equal to time_seconds
                            
                         #downloading put value in cloud
                            if flag == "pub":
                                cloud[ExecutableID] = ExecutableID
                                
                            latency_buffer = f"Latency to buffer for ExecutableID {ExecutableID}: {remaining_time}"
                            latency_cloud = ""  # Set cloud latency to blank
                            latency_cache = ""
                            
                            
                            #Increment the counter
                            buffer_counter += 1
                          
            #CAche hit it is                            
            if  ExecutableID in cache:
                
                #Update credit in cache
                PREPARETOCACHE(cache, ExecutableID, edge, queue, flag)
                              
                latency_cloud = ""  # Set other latencies to blank
                latency_buffer = ""
                
                if flag == 'pub':
                    cloud[ExecutableID] = ExecutableID
                    latency_cache = f"Latency to cloud for ExecutableID {ExecutableID}: 0" 
                                                   
                elif flag == 'priv':
                    latency_cache = f"Latency to next edge for ExecutableID {ExecutableID}: 0"
   
            #Calculate the number of cache hits
            num_cache_hits = len(cache_hits)
            
            # Check if any conditions were satisfied and 
            if latency_cloud or latency_buffer or latency_cache:
               
               # Add latencies that satisfy conditions to the total latency
                if latency_cloud:
                    
                    try:                       
                        # Extract the numeric value from the string
                        latency_cloud_value = float(latency_cloud.split(":")[1].strip())
                        total_latency += latency_cloud_value
                        
                    except (ValueError, IndexError):
                        total_latency += float(latency_cloud)
                
                         
                if latency_buffer:
                    try:
                        
                      # Extract the numeric value from the string
                        latency_buffer_value = float(latency_buffer.split(":")[1].strip())
                        total_latency += latency_buffer_value
                        
                    except (ValueError, IndexError):
                        total_latency += float(latency_buffer)


                #print the values in file
                if flag == 'priv':   
                    print(f"ExecutableID: {ExecutableID}, SubmitTime: {SubmitTime_list[edge][row_number]}, {latency_cloud}, {latency_buffer}, {latency_cache},Number of cache hits: {num_cache_hits},Total Latency: {total_latency},delayed_hit: {buffer_counter},forward_counter: {forward_counter},skipped_counter: {skipped_counter[edge]}, cost: {exec_cost_cache},cost_counter: {cost_counter}, {latency_edge}, {latency_edge_row} ", file=file)
                   
                elif flag == 'pub':   
                    print(f"ExecutableID: {ExecutableID}, From private edge: {pubq_edge_in_data[edge][row_number] + 1}, Row number: {pubq_index_in_data[edge][row_number] + 1}, SubmitTime: {pubq_SubmitTime_list[edge][row_number]}, {latency_cloud}, {latency_buffer}, {latency_cache},Number of cache hits: {num_cache_hits},Total Latency: {total_latency},delayed_hit: {buffer_counter}, forward_counter: {forward_counter}, cost: {exec_cost_cache},cost_counter: {cost_counter}", file=file)
               
           
            # This block will be executed if none of the conditions above were satisfied       
            else:
                print("No conditions were satisfied for ExecutableID: ", ExecutableID, file=file)
                
            # Incrementing row values    
            row_number = row_number+1
            
            # total length of queue    
            total_entries =  len(queue) 
            
            # let wait if any forward entry for public queue come after some wait
            # it will wait and break if all private queue threads stop or new entrycomes
            if flag == 'pub': 
                      
                while True:
                    # if queue reach its end and there is no more entry left
                    if row_number == total_entries:
        
                        # if all private queues stop then no new entry will come, so why to wait
                        if not any(thread.is_alive() for thread in threads[:mod]):
                            total_entries = len(queue)
                            break
        
                        # wait for 1 sec and update the list
                        time.sleep(1)
                        total_entries = len(queue) 
        
                    else:
                     # list is updated and there are new entries in queue, no more wait
                        break
     
     
            #checking  conditing to stop         
            if (row_number < total_entries): 
                if flag == 'priv':
                    SubmitTime  = SubmitTime_list[edge][row_number]
        
                elif flag == 'pub':
                    SubmitTime  = pubq_SubmitTime_list[edge][row_number]

            
            
############################################################################
    


# managing cache using landlord
def LLCA(cache, temp, ExecutableIDlocal,resources_dict):
    cpu = resources_dict[ExecutableIDlocal][0]
    mem = resources_dict[ExecutableIDlocal][1]
    disk = resources_dict[ExecutableIDlocal][2]
    Landlord(cache, C, ExecutableIDlocal,cpu,mem,disk,temp) 



######################################################################################


# CAlling by threading
# Create an empty list to store thread references
threads = []

# Create and start threads
# Call the HANDLE_SERVICE_REQUEST function with the private queue
for i in range(mod):
    server_name = f'server{i+1}_priv'
    thread = threading.Thread(target=HANDLE_SERVICE_REQUEST, args=(i, priv_q[i], 'priv', priv_cache[i], server_name))
    threads.append(thread)
    thread.start()
           
# Call the HANDLE_SERVICE_REQUEST function with the public queue
for i in range(mod):
    server_name = f'server{i+1}_pub'
    thread = threading.Thread(target=HANDLE_SERVICE_REQUEST, args=(i, pub_q[i], 'pub', pub_cache[i], server_name))
    threads.append(thread)
    thread.start()

# Join all threads
for thread in threads:
    thread.join()

 
 
#######################################################################################
      
    
#calling individual
     
# HANDLE_SERVICE_REQUEST(0, priv_q[0], 'priv' ,priv_cache[0], 'rr_case1')

# HANDLE_SERVICE_REQUEST(0, priv_q[0], 'priv' ,priv_cache[0], 'server1_priv')

# HANDLE_SERVICE_REQUEST(1, priv_q[1], 'priv' ,priv_cache[1], 'server2_priv')

# HANDLE_SERVICE_REQUEST(0, pub_q[0], 'pub' ,pub_cache[0],  'server1_pub')

# HANDLE_SERVICE_REQUEST(1, pub_q[1], 'pub' ,pub_cache[1], 'server2_pub')



##################################################################################



#printing public and private queue for each edge   
for i in range(mod):
    with open(f'pub_q{i+1}.txt', 'w') as file:
        for item in pub_q[i]:
            file.write(f"{item}\n")
    
    with open(f'priv_q{i+1}.txt', 'w') as file:
        for item in priv_q[i]:
            file.write(f"{item}\n")
   
    
    
###########################################################################


# Print desired file to check

# with open('datasize.txt', 'w') as file:
#       for item in data_size:
#         file.write(f"{item}\n")
       
# with open('datasize2.txt', 'w') as file:
#      for item in Mi_bytes[1]:
#        file.write(f"{item}\n")
       
# with open('datasize3.txt', 'w') as file:
#      for item in skipped_rows[0]:
#        file.write(f"{item}\n")
       
# with open('datasize.txt', 'w') as file:
#      for item in skipped_rows[1]:
#        file.write(f"{item}\n")
       
# with open('datasize5.txt', 'w') as file:
#      for key, value in Global_time_executables.items():
#         file.write(f"{key}: {value}\n")
        
# with open('datasize6.txt', 'w') as file:
#      for key, value in time_for_executabletoedge[0].items():
#              file.write(f"{key}: {value}\n")
