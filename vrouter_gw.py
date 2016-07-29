#!/usr/bin/python
from vnc_api import vnc_api
import yaml
from requests.exceptions import *
from cfgm_common.exceptions import *
import pdb

class VrouterGw(object):
    def __init__(self,filename=None):
        self.vroutergw_params={}
        self.vh=None

        with open('params.yaml','r') as fh:
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
    def add_tasks(self):
        # Add/delete/display a vrouter gateway object
        if 'gw_vrouters' in self.vroutergw_params['resource'].keys():
            for gw_vrouter in self.vroutergw_params['resource']['gw_vrouters']:
                if gw_vrouter['operation'] == 'noop':
                    pass
                elif gw_vrouter['operation'] == 'add':
                    self.AddRouter( hostname=gw_vrouter['name'],
                                    vendor=gw_vrouter['vendor'],
                                    model=gw_vrouter['model'],
                                    ip_addr=gw_vrouter['ip'])
                else:
                    pass

        if 'physical_intfs' in self.vroutergw_params['resource'].keys():
            for phys_intf in self.vroutergw_params['resource']['physical_intfs']:
                if phys_intf['operation'] == 'noop':
                    pass
                elif phys_intf['operation'] == 'add':
                    self.AddPort(name=phys_intf['name'],
                                 router=phys_intf['connected_vrouter'])
                else:
                    pass
        sg=None
        fip=None
        if 'baremetalservers' in self.vroutergw_params['resource'].keys():
            for bms in self.vroutergw_params['resource']['baremetalservers']:
                if 'sg' in bms.keys():
                    sg=bms['sg']
                if 'fip' in bms.keys():
                    fip=bms['fip']
                if bms['operation'] == 'noop':
                    pass
                elif bms['operation'] == 'add':
                    self.AddBMS(name=bms['name'],
                                mac=bms['mac'],
                                ip_addr=bms['fixed_ip'],
                                vn=bms['vn'],
                                vlan=bms['vlan'],
                                port=bms['phy_intf'],
                                connected_routers=bms['connected_vrouters'],
                                fip_id=fip,
                                sg_list=sg)

    def del_tasks(self):
        if 'baremetalservers' in self.vroutergw_params['resource'].keys():
            sg=None
            fip=None
            for bms in self.vroutergw_params['resource']['baremetalservers']:
                if 'sg' in bms.keys():
                    sg=bms['sg']
                if 'fip' in bms.keys():
                    fip=bms['fip']
                if bms['operation'] == 'noop':
                    pass
                elif bms['operation'] == 'delete':
                    self.DelBMS(name=bms['name'],connected_routers=bms['connected_vrouters'],port=bms['phy_intf'],vlan=bms['vlan'],fip_id=fip)
                else:
                    pass
        if 'physical_intfs' in self.vroutergw_params['resource'].keys():
            for phys_intf in self.vroutergw_params['resource']['physical_intfs']:
                if phys_intf['operation'] == 'noop':
                    pass
                elif phys_intf['operation'] == 'delete':
                    self.DelPort(name=phys_intf['name'],router=phys_intf['connected_vrouter'])
                else:
                    pass
        if 'gw_vrouters' in self.vroutergw_params['resource'].keys():
            for gw_vrouter in self.vroutergw_params['resource']['gw_vrouters']:
                if gw_vrouter['operation'] == 'noop':
                    pass
                elif gw_vrouter['operation'] == 'delete':
                    self.DelRouter(name=gw_vrouter['name'])
                else:
                    pass

    def AddRouter(self,hostname,ip_addr,vendor=None,model=None):
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
            return False
        physical_router_obj=self.vh.physical_router_read(id=uuid)
        vrouter_obj=self.vh.virtual_router_read(fq_name=[u'default-global-system-config',hostname])
        physical_router_obj.set_virtual_router(vrouter_obj)
        self.vh.physical_router_update(physical_router_obj)
        return uuid

    def DelRouter(self,name):
        try:
            self.vh.physical_router_delete(fq_name=['default-global-system-config',name])
            print "Successfully deleted router %s" %(name)
        except Exception as e:
            print "Unable to delete the physical router %s" %(name)
            print str(e)
            return False
    def AddPort(self,name,router):
        try:
            parent=self.vh.physical_router_read(fq_name=['default-global-system-config',router])
        except Exception as e:
            print "Unable to get the parent object"
            print str(e)
            return False
        pif = vnc_api.PhysicalInterface(name=name, parent_obj=parent)
        try:
            uuid=self.vh.physical_interface_create(pif)
            print "Successfully created physical inetrface %s for router %s, uuid is %s" %(name,router,uuid)
        except Exception as e:
            print "Unable to create the interface"
            print str(e)
            return False
    def DelPort(self,name,router):
        try:
            self.vh.physical_interface_delete(fq_name=['default-global-system-config',router,name])
            print "Successfully deleted physical inetrface %s for router %s" %(name,router)
        except Exception as e:
            print "Unable to delete the interface"
            print str(e)
            return False
    def AddBMS(self,name,mac,ip_addr,vn,vlan,connected_routers,port,sg_list=None,fip_id=None):
        try:
            proj=self.vh.project_read(fq_name=[u'default-domain',self.vroutergw_params['credentials']['tenant']])
        except Exception as e:
            print "Unable to read the project object"
            print str(e)
        vmi=vnc_api.VirtualMachineInterface(name=name,parent_obj=proj)
        mac_obj = vnc_api.MacAddressesType()
        mac_obj.add_mac_address(mac)
        vmi.set_virtual_machine_interface_mac_addresses(mac_obj)
        vmi.set_display_name(name)
        vn_obj= self.vh.virtual_network_read(fq_name = [u'default-domain', self.vroutergw_params['credentials']['tenant'], vn])
        vmi.add_virtual_network(vn_obj)
        try:
            uuid=self.vh.virtual_machine_interface_create(vmi)
            print "Successfully created the VMI %s , uuid is %s" %(name,uuid)
        except Exception as e:
            print "Unable to create the VMI"
            print str(e)
        iip =vnc_api.InstanceIp(name=name)
        iip.set_instance_ip_family('v4')
        print "%s" %(uuid)
        vmi=self.vh.virtual_machine_interface_read(id=uuid)
        iip.add_virtual_machine_interface(vmi)
        iip.add_virtual_network(vn_obj)
        iip.set_instance_ip_address(ip_addr)
        try:
            uuid=self.vh.instance_ip_create(iip)
            print "Successfully created the instance IP address object , uuid is %s" %(uuid)
        except Exception as e:
            print "Unable to create the instance IP object"
            print str(e)
        
        # Associate the FIP and the SG
        if sg_list:
            for i in sg_list:
                sg=self.vh.security_group_read(fq_name=[u'default-domain', self.vroutergw_params['credentials']['tenant'],i])
                vmi.add_security_group(sg)
                self.vh.virtual_machine_interface_update(vmi)
        if fip_id:
            fip=self.vh.floating_ip_read(id=fip_id)
            fip.set_virtual_machine_interface(vmi)
            self.vh.floating_ip_update(fip)

        # Add the logical interface and associate the VMI
        for phys_rtr in connected_routers:
            pif_fq_name=[u'default-global-system-config', phys_rtr, port]
            pif_obj=self.vh.physical_interface_read(fq_name=pif_fq_name)
            lif_name="%s.%s" %(str(port),str(vlan))
            lif_obj=vnc_api.LogicalInterface(name=lif_name, parent_obj=pif_obj, display_name=lif_name)
            lif_obj.set_logical_interface_vlan_tag(vlan)
            try:
                uuid=self.vh.logical_interface_create(lif_obj)
                print "Successfully created the logical interface %s, uuid is %s" %(lif_name,uuid)
            except Exception as e:
                print "Unable to create the logical interface"
                print str(e)
            lif_obj=self.vh.logical_interface_read(id=uuid)
            vmi_obj=self.vh.virtual_machine_interface_read(fq_name=[u'default-domain', self.vroutergw_params['credentials']['tenant'],name])
            lif_obj.add_virtual_machine_interface(vmi_obj)
            self.vh.logical_interface_update(lif_obj)

    def DelBMS(self,name,connected_routers,port,vlan,fip_id=None):
        for rtr in connected_routers:
            lif_name="%s.%s" %(port,str(vlan))
            lif_fq_name=[u'default-global-system-config',rtr,port,lif_name]
            try:
                self.vh.logical_interface_delete(fq_name=lif_fq_name)
                print "Successfully deleted the logical interface for the BMS"
            except Exception as e:
                print "Unable to delete the object"
                print str(e)
        if fip_id:
            fip=self.vh.floating_ip_read(id=fip_id)
            vmi=self.vh.virtual_machine_interface_read(fq_name=[u'default-domain', self.vroutergw_params['credentials']['tenant'], name])
            fip.del_virtual_machine_interface(vmi)
            self.vh.floating_ip_update(fip)
        try:
            self.vh.instance_ip_delete(fq_name=[name])
            self.vh.virtual_machine_interface_delete(fq_name=[u'default-domain', self.vroutergw_params['credentials']['tenant'], name])
        except Exception as e:
            print "Failed to delete the IIP and the VMI"
            print str(e)

if __name__=='__main__':
    v=VrouterGw()
    v.add_tasks()
    v.del_tasks()
