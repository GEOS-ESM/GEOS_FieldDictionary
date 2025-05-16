#!/usr/bin/env python3
from yaml import load,dump
import argparse
import os

def get_block(cvs_file):

    temp = cvs_file[0].split(' ')
    state_type = temp[1][1:]
    component = temp[4].strip()
    i=2
    for line in cvs_file[2:]:
        if "spec for" in line:
            break
        i=i+1
    return component,state_type,i
        

def get_unique_long_names(cvs_file):

    i_start = 0
    i_end = 0
    n_lines = len(cvs_file)
    long_names = []
    while i_start < n_lines-1:

       comp_name,state_type,i_end = get_block(cvs_file[i_start:])
       for i in range(i_end-2):
           line = cvs_file[i_start+2+i]
           values = line.split(',')
           long_name = values[2]
           if long_name not in long_names:
              long_names.append(long_name)
       i_start = i_start + i_end

    return long_names

def append_item(old_dict,units,comp_name,state_type,item_type):

    if old_dict:
       #old_units = old_dict["units"]
       #new_units = old_units
       #new_units.append(units)
       #old_item_type = old_dict["item_type"]
       #new_item_type = old_item_type
       #new_item_type.append(item_type)
       old_component = old_dict["component"]
       new_component = old_component
       new_component.append(comp_name+"_"+state_type)
       #new_dict = {"units":new_units,"item_type":new_item_type,"component":new_component}
       new_dict = {"component":new_component}
    else:
       #new_dict = {"units":[units],"item_type":[item_type],"component":[comp_name+"_"+state_type]}
       new_dict = {"component":[comp_name+"_"+state_type]}
    return new_dict

def get_long_name_map(cvs_file):

    i_start = 0
    i_end = 0
    n_lines = len(cvs_file)
    long_names = {}
    while i_start < n_lines-1:

       comp_name,state_type,i_end = get_block(cvs_file[i_start:])
       for i in range(i_end-2):
           line = cvs_file[i_start+2+i]
           values = line.split(',')
           long_name = values[2].strip()
           units = values[3].strip()
           item_type = values[5].strip()
           if long_name not in long_names:
              existing_dict = {}
              updated_dict = append_item(existing_dict,units,comp_name,state_type,item_type)
              long_names.update({long_name:updated_dict})
           else:
              existing_dict = long_names[long_name]
              updated_dict = append_item(existing_dict,units,comp_name,state_type,item_type)
              long_names.update({long_name:updated_dict})
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
   long_names = get_unique_long_names(input_rc)
   long_name_map = get_long_name_map(input_rc)

   if input_file[:2] == "./":
      full_path = input_file[2:]
   else:
      full_path = input_file

   split_string = full_path.rsplit(".",1)
   output_file = split_string[0]+"_by_long_name.yaml"

   f = open(output_file,"w")

   output_yaml = dump(long_name_map)+"\n"

   lines = output_yaml.split("\n")
   for line in lines:
       f.write(line+"\n")
   f.close()

#  do by component
   component_map = get_component_map(input_rc)

   if input_file[:2] == "./":
      full_path = input_file[2:]
   else:
      full_path = input_file

   split_string = full_path.rsplit(".",1)
   output_file = split_string[0]+"_by_component.yaml"

   f = open(output_file,"w")

   output_yaml = dump(component_map)+"\n"

   lines = output_yaml.split("\n")
   for line in lines:
       f.write(line+"\n")
   f.close()
