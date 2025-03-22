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
			shutil.copy2(original_copy_file,target_copy_file)
		path_now+=target_splited[index_of_splited]
		path_now+='/'
def size(s,uit):
	units=['B','KB','MB','GB','TB']
	now=uit
	while True:
		if s<1024 or now==len(units)+1:
			return f'{round(s,2)}{units[now]}'
		else:
			s=s/1024
			now+=1
#root dir,you must copy 'indexes' and 'objects' on .minecraft/assets/ to the dir
root_dir='/'.join(__file__.split('/')[0:-1])+'/'
#result dir,it will be create on root dir
result_dir='result'
#open indexes dir
os.chdir(f'{root_dir}indexes/')
#list all item
indexes=os.listdir()
all_indexes_count=len(indexes)
index_of_all_indexes=0
for index in indexes:
	index_of_all_indexes+=1
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
		all_files_count=len(target_files)
		index_of_all_files=0
		for target_file in target_files:
			index_of_all_files+=1
			#get dir name and file name in objects dir
			original_file=objects[target_file]['hash']
			original_file_size=size(objects[target_file]['size'],0)
			
			splited_dirs=original_file[0:2]
			#get absolute path
			original_path=f'{root_dir}objects/{splited_dirs}/{original_file}'
			target_path=f'{root_dir}{result_dir}/{result_dir_of_index}/{target_file}'
			if map_text=='':
			    map_text+=f'{all_files_count} files,{index_of_all_indexes} of {all_indexes_count}\n'
			
			tip_text=f'{result_dir_of_index}:{original_file}->./{target_file} size:{original_file_size}'
			tip_print=f'\033[38;2;0;128;255m{index_of_all_files}\033[0m/\033[38;2;0;255;0m{all_files_count} \033[38;2;0;255;0m{result_dir_of_index}\033[0m(\033[38;2;0;128;255m{index_of_all_indexes}\033[0m/\033[38;2;0;255;0m{all_indexes_count}\033[0m):\033[38;2;0;128;255m{original_file}\033[0m->\033[38;2;128;128;0m./{target_file}\033[0m'
			print(tip_print)
			map_text+=tip_text
			map_text+='\n'
			
			copy_and_mkdir(original_path,target_path)

		#write map file
		open(f'{root_dir}{result_dir}/{result_dir_of_index}/.map.txt','w').write(map_text)
		print(f'Process \033[38;2;0;128;255m{result_dir_of_index}\033[0m done!')
print(f'All \033[38;2;0;255;0m{all_indexes_count}\033[0m processes done!')