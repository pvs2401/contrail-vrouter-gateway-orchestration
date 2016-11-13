#!/usr/bin/python
from vnc_api import vnc_api
import os
import argparse
import sys

class UpdateVMI(object):
	def __init__(self):
		self._domain_name='default-domain'
		self._args=self.parse_args()
		if self._args['ip']:
			self._api_server=self._args['ip']
		else:
			self._api_server='localhost'
		if self._args['port']:
			self._api_port=self._args['port']
		else:
			self._api_port='8082'
		if self._args['user']:
			self._username=self._args['user']
		else:
			try:
				self._username=os.environ['OS_USERNAME']
			except KeyError:
				print "Either source the openstack credentials or provide the credentials as command line argument"
				sys.exit()
		if self._args['password']:
			self._password=self._args['password']
		else:
			try:
				self._password=os.environ['OS_PASSWORD']
			except KeyError:
				print "Either source the openstack credentials or provide the credentials as command line argument"
				sys.exit()
		if self._args['tenant']:
			self._tenant=self._args['tenant']
		else:
			try:
				self._tenant=os.environ['OS_TENANT_NAME']
			except KeyError:
				print "Either source the openstack credentials or provide the credentials as command line argument"
				sys.exit()
		self._cmd=self._args['cmd']
		if self._args['cmd'] in ('enable' , 'disable'):
			if self._args['vmi']:
				self._vmi=self._args['vmi']
			else:
				raise RuntimeError("VMI is required for enable and disable actions")
				sys.exit()
		self.vh=vnc_api.VncApi(api_server_host = self._api_server, api_server_port=self._api_port,username=self._username,password=self._password,tenant_name=self._tenant)

	def RunCmd(self):
		if self._args['cmd']=='print':
			self.dump_vmi(self.vh)
		elif self._args['cmd'] in ('enable','disable'):
			self.modify_policy(self.vh,self._vmi,self._cmd)
		return True

	@staticmethod
	def dump_vmi(vh):
		print '{:45} {:40} {:20} {:20} {:15}'.format('uuid','vn_fq_name','mac_address','ip_address','policy_disabled')
		print '---------------------------------------------------------------------------------------------------------------------------------------------------'
		for var1 in vh.virtual_machine_interfaces_list()['virtual-machine-interfaces']:
			vmi_uuid=var1['uuid']
			vmi=vh.virtual_machine_interface_read(id=vmi_uuid)
			vn_fq_name=':'.join(vmi.virtual_network_refs[0]['to'])
			vmi_mac=vmi.get_virtual_machine_interface_mac_addresses().mac_address[0]
			vmi_iip=vmi.get_instance_ip_back_refs()[0]['uuid']
			vmi_ip=vh.instance_ip_read(id=vmi_iip).instance_ip_address
			vmi_policy_flag='True' if vmi.get_virtual_machine_interface_disable_policy() else 'False'
			print '{:45} {:40} {:20} {:20} {:15}'.format(vmi_uuid,vn_fq_name,vmi_mac,vmi_ip,vmi_policy_flag)
		return True

	@staticmethod
	def modify_policy(vh,vmi_uuid,action):
		if action=='enable':
			print "Enabling the policy for the vmi %s" %(vmi_uuid)
			vmi=vh.virtual_machine_interface_read(id=vmi_uuid)
			vmi.set_virtual_machine_interface_disable_policy(False)
			vh.virtual_machine_interface_update(vmi)
		else:
			print "Disabling the policy for the vmi %s" %(vmi_uuid)
			vmi=vh.virtual_machine_interface_read(id=vmi_uuid)
			vmi.set_virtual_machine_interface_disable_policy(True)
			vh.virtual_machine_interface_update(vmi)
		return True

	def parse_args(self):
		parser = argparse.ArgumentParser(description='Enable/disable policy on a VMI')
		parser = argparse.ArgumentParser()
		parser.add_argument('--ip', help='API Server IP address defaults to localhost' )
		parser.add_argument('--port', help='API Server port defaults to 8082' )
		parser.add_argument('--user', help='API server authentication username defaults to Openstack ENV variable OS_USERNAME' )
		parser.add_argument('--password', help='API server authentication password defaults to Openstack ENV variable OS_PASSWORD' )
		parser.add_argument('--tenant', help='API server authentication tenant defaults to Openstack ENV variable OS_TENANT_NAME' )
		parser.add_argument('--vmi', help='VMI UUID if the command is enable or disable')
		parser.add_argument('cmd', choices=['enable', 'disable', 'print'], help='Whether to enable or disable the policy on a VMI or else just print the VMI details')
		args = parser.parse_args()
		return vars(args)
if __name__=='__main__':
	test=UpdateVMI()
	test.RunCmd()
