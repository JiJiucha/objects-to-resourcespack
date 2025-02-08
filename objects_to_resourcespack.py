import os
import json
import shutil
#copy file to another file,if the any dir doesn't exist,the function will create it
def copy_and_mkdir(original_copy_file:str,target_copy_file:str):
	target_splited=target_copy_file.split('/')
	target_splited.pop(0)
	path_now='/'
	for index_of_splited in range(len(target_splited)):
		try:
			os.chdir(path_now)
		except:
			os.mkdir(path_now)
		if(index_of_splited==len(target_splited)-1):
			shutil.copy(original_copy_file,target_copy_file)
		path_now+=target_splited[index_of_splited]
		path_now+='/'
#root dir,you must copy 'indexes' and 'objects' on .minecraft/assets/ to the dir
root_dir='/'.join(__file__.split('/')[0:-1])+'/'
#result dir,it will be create on root dir
result_dir='result'
#open indexes dir
os.chdir(f'{root_dir}indexes/')
#list all item
indexes=os.listdir()

for index in indexes:
    #remove the '.json'
	result_dir_of_index=index[0:-5]
	with open(f'{root_dir}indexes/{index}') as index_file:
		map_text=''
		os.chdir('..')
		#json to dict from file
		index_dict=json.load(index_file)
		#get map dict
		objects=index_dict['objects']
		#get all target file
		target_files=objects.keys()
		for target_file in target_files:
			
			#get dir name and file name in objects dir
			original_file=objects[target_file]['hash']
			splited_dirs=original_file[0:2]
			#get absolute path
			original_path=f'{root_dir}objects/{splited_dirs}/{original_file}'
			target_path=f'{root_dir}{result_dir}/{result_dir_of_index}/{target_file}'
			
			tip_text=f'{result_dir_of_index}:{original_file}->{target_file}'
			print(tip_text)
			map_text+=tip_text
			map_text+='\n'
			
			copy_and_mkdir(original_path,target_path)
			
		#write map file
		open(f'{root_dir}{result_dir}/{result_dir_of_index}/.map.txt','w').write(map_text)
			
			