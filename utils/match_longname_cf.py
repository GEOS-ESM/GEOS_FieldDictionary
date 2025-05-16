#!/usr/bin/env python3
import yaml
import argparse
import xml.etree.ElementTree as ET

def parse_args():
    p = argparse.ArgumentParser(description='Converter for old extdata rc files to yaml format')
    p.add_argument('cf_file',type=str,help='example file',default=None)
    p.add_argument('geos_file',type=str,help='example file',default=None)
    return vars(p.parse_args())

if __name__ == '__main__':

   args = parse_args()
   cf_file = args['cf_file']
   geos_long_names_file = args['geos_file']

   cf_names = ET.parse(cf_file)
   myroot = cf_names.getroot()

   cf_names_list = []
   for x in myroot.findall('entry'):
      cf_names_list.append(x.attrib['id'].strip())

   cf_alias_list = []
   for x in myroot.findall('alias'):
      cf_alias_list.append(x.attrib['id'].strip())


   print("Size of cf name list and cf alias list")
   print(len(cf_names_list),len(cf_alias_list))


   with open(geos_long_names_file,'r') as gfile:
      geos_long_names = yaml.load(gfile, Loader=yaml.FullLoader)

   ifound1 = 0
   for name in geos_long_names:
       if name.strip() in cf_names_list:
          ifound1 = ifound1 + 1
          print(name)

   ifound2 = 0
   for name in geos_long_names:
       if name.strip() in cf_alias_list:
          ifound2 = ifound2 + 1
          print(name)
   
   print("This name geos long names were round in cf list out of total number of unique GEOS long name")
   print(ifound1+ifound2,len(geos_long_names.keys()))
