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

    comp_with_long = {}
    short_with_long = {}

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
              short_name = values[1].strip()
              long_name = values[2].strip()
              units = values[3].strip()
              item_type = values[5].strip()

              if (long_name not in long_names) and (item_type == "esmf_field"):
                 long_names.update({long_name:{"units":units,"incomplete":True}})

              # update list components with long_name
              if (item_type == "esmf_field"):
                 if (long_name in comp_with_long):
                    old_list = comp_with_long[long_name]
                    if comp_name not in old_list:
                       old_list.append(comp_name)
                       comp_with_long[long_name]=old_list
                 else:
                    comp_with_long[long_name]=[comp_name]
                    old_list = [comp_name]
                 # now add to long_names
                 long_names[long_name].update({"components":old_list})
              if (item_type == "esmf_field"):
                 if (long_name in short_with_long):
                    old_list = short_with_long[long_name]
                    if short_name not in old_list:
                       old_list.append(short_name)
                       short_with_long[long_name]=old_list
                 else:
                    short_with_long[long_name]=[short_name]
                    old_list = [short_name]
                 # now add to long_names
                 long_names[long_name].update({"short_names":old_list})


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
    return vars(p.parse_args())

if __name__ == '__main__':

   args = parse_args()
   input_file = args['input']
   f = open(input_file,"r")
   input_rc = f.readlines()
   f.close()

#  do by long_name
   long_name_map = {}
   exclude_internal = False
   long_name_map = get_long_name_map(input_rc,long_name_map,exclude_internal)


   output_file = "geos_long_names.yaml"
   f = open(output_file,"w")
   output_yaml = dump(long_name_map)+"\n"
   lines = output_yaml.split("\n")
   for line in lines:
       f.write(line+"\n")
   f.close()

#  component
   component_map = {}
   component_map = get_component_map(input_rc)

   output_file = "geos_components.yaml"

   f = open(output_file,"w")

   output_yaml = dump(component_map)+"\n"

   lines = output_yaml.split("\n")
   for line in lines:
       f.write(line+"\n")
   f.close()

 
