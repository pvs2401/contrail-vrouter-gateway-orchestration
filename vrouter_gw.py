#!/usr/bin/python
from vnc_api import vnc_api
import yaml
from requests.exceptions import *
from cfgm_common.exceptions import *


class VrouterGw(object):
    def __init__(self,filename=None):
        self.vroutergw_params={}
        self.vh=None

        with open('params1.yaml','r') as fh:
            self.vroutergw_params.update(yaml.load(fh))

        self.vh=self.ConnectApiServer(host=self.vroutergw_params['credentials']['api_server'],
                                      port=self.vroutergw_params['credentials']['api_port'],
                                      user=self.vroutergw_params['credentials']['user'],
                                      password=self.vroutergw_params['credentials']['password'],
                                      tenant=self.vroutergw_params['credentials']['tenant'])

    @staticmethod
    def ConnectApiServer(host='localhost',port='8082',user='admin',password='contrail123',tenant='admin'):
        try:
            vh = vnc_api.VncApi(api_server_host=host,api_server_port=port,username=user,password=password,tenant_name=tenant)
            return vh
        except RuntimeError:
            print "Failed to connect !!!"
            raise;
    def tasks(self):
        # Add/delete/display a vrouter gateway object
        if 'gw_vrouters' in self.vroutergw_params['resource'].keys():
            for gw_vrouter in self.vroutergw_params['resource']['gw_vrouters']:
                if gw_vrouter['operation'] == 'noop':
                    pass
                else:
                    self.VncPhyRouter(operation=gw_vrouter['operation'],
                                    hostname=gw_vrouter['name'],
                                    vendor=gw_vrouter['vendor'],
                                    model=gw_vrouter['model'],
                                    ip_addr=gw_vrouter['ip'])
        elif 'physical_intfs' in self.vroutergw_params['resource'].keys():
            for phys_intf in self.vroutergw_params['resource']['physical_intfs']:
                if phys_intf['operation'] == 'noop':
                    pass
                else:
                    self.VncPhyIntf(name=phys_intf['name'],
                                    operation=phys_intf['operation'],
                                    physical_rtr=phys_intf['connected_vrouter'])
        elif 'baremetalservers' in self.vroutergw_params['resource'].keys():
            for bms in self.vroutergw_params['resource']['baremetalservers']:
                if bms['operation'] == 'noop':
                    pass
                else:
                    self.VncVmi(operation=bms['operation'],
                                vn=bms['vn'],
                                mac=bms['mac'],
                                fixed_ip=bms['fixed_ip'],
                                phy_intf=bms['phy_intf'],
                                vlan_id=bms['vlan'])
        else:
            pass
    def VncPhyRouter(self,hostname,vendor,model,ip_addr,operation):
        try:
            gs=self.vh.global_system_config_read(fq_name=['default-global-system-config'])
        except Exception as e:
            print "Unable to read the default-global-system-config"
            print str(e)
            exit(1)
        physical_router_obj = vnc_api.PhysicalRouter(name = hostname,
                                                    parent_obj = gs,
                                                    physical_router_management_ip = ip_addr,
                                                    physical_router_dataplane_ip = ip_addr,
                                                    physical_router_vendor_name = vendor,
                                                    physical_router_product_name = model)
        try:
            uuid=self.vh.physical_router_create(physical_router_obj)
            print "Successfully created physical router %s, uuid is %s" %(hostname, uuid)
        except Exception as e:
            print "Unable to create the physical router"
            print str(e)
            exit(1)
        return uuid

if __name__=='__main__':
    v=VrouterGw()
    import pdb;pdb.set_trace()
