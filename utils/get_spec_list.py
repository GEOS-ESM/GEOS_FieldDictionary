#!/usr/bin/env python3
from yaml import load,dump
import argparse
import os

def get_block(cvs_file):

    temp = cvs_file[0].split(' ')
    state_type = temp[1][1:].strip()
    component = temp[4].strip()
    i=2
    for line in cvs_file[2:]:
        if "spec for" in line:
            break
        i=i+1
    return component,state_type,i
        

def get_long_name_map(cvs_file,long_names,exclude_internal):

    i_start = 0
    i_end = 0
    n_lines = len(cvs_file)
    while i_start < n_lines-1:

       comp_name,state_type,i_end = get_block(cvs_file[i_start:])
       do_block = True
       if (state_type == "INTERNAL") and exclude_internal:
          do_block = False

       if do_block:
          for i in range(i_end-2):
              line = cvs_file[i_start+2+i]
              values = line.split(',')
              long_name = values[2].strip()
              units = values[3].strip()
              item_type = values[5].strip()
              if (long_name not in long_names) and (item_type == "esmf_field"):
                 long_names.update({long_name:{"units":units,"long_names":long_name}})
       i_start = i_start + i_end

    return long_names

def get_component_map(cvs_file):

    i_start = 0
    i_end = 0
    n_lines = len(cvs_file)
    components = {}
    while i_start < n_lines-1:

       comp_name,state_type,i_end = get_block(cvs_file[i_start:])
       comp_map = {}
       for i in range(i_end-2):
           line = cvs_file[i_start+2+i]
           values = line.split(',')
           long_name = values[2].strip()
           units = values[3].strip()
           item_type = values[5].strip()
           comp_map.update({long_name:{"units":units,"item_type":item_type}})
       components.update({comp_name+"_"+state_type:comp_map})
       i_start = i_start + i_end

    return components

def parse_args():
    p = argparse.ArgumentParser(description='Converter for old extdata rc files to yaml format')
    p.add_argument('input',type=str,help='example file',default=None)
    p.add_argument('output',type=str,help='example file',default=None)
    p.add_argument('--exclude_internal',action=argparse.BooleanOptionalAction,help='example file')
    return vars(p.parse_args())

if __name__ == '__main__':

   args = parse_args()
   input_files = args['input']
   output_file = args['output']
   exclude_internal = args['exclude_internal']
   if exclude_internal:
      print("was true")
   else:
      print("was false")
   f = open(input_files,"r")
   input_file_list=f.readlines()
   f.close()

   
   long_name_map = {}
   for input_file in input_file_list:
      f = open(input_file.rstrip(),"r")
      input_rc = f.readlines()
      f.close()
      long_name_map = get_long_name_map(input_rc,long_name_map,exclude_internal)

#     component
      component_map = {}
      component_map = get_component_map(input_rc)
      split_file = input_file.split(".")
      comp_file = split_file[0]+".yaml"
      f = open(comp_file,"w")
      output_yaml = dump(component_map)+"\n"
      lines = output_yaml.split("\n")
      for line in lines:
          f.write(line+"\n")
      f.close()



   f = open(output_file,"w")
   output_yaml = dump(long_name_map)+"\n"
   lines = output_yaml.split("\n")
   for line in lines:
       f.write(line+"\n")
   f.close()

 
