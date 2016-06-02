from qom import \
    QOMType

from source import \
    Source, \
    Type, \
    Initializer, \
    Function

from machine_description import \
    MachineNode, \
    DeviceNode, \
    SystemBusDeviceNode, \
    PCIExpressDeviceNode, \
    BusNode, \
    SystemBusNode, \
    PCIExpressBusNode, \
    IRQLine, \
    IRQHub, \
    QOMPropertyTypeLink, \
    QOMPropertyTypeString, \
    QOMPropertyTypeBoolean, \
    QOMPropertyTypeInteger, \
    MemoryNode, \
    MemoryAliasNode, \
    MemoryRAMNode, \
    MemoryROMNode

from common import \
    sort_topologically

import os.path
from qemu.machine_description import DeviceNode, IRQLine, PCIExpressDeviceNode
from __builtin__ import isinstance

class UnknownMachineNodeType(Exception):
    def __init__(self, t):
        Exception.__init__(self, t)

class UnknownBusBridgeType(Exception):
    def __init__(self, primary_bus, secondary_bus):
        Exception.__init__(self, "%s <-> %s" % (str(type(primary_bus)), str(type(secondary_bus))))

class IncorrectPropertyValue(Exception):
    pass

class UnknownPropertyType(Exception):
    pass

class UnknownMemoryNodeType(Exception):
    def __init__(self, t):
        Exception.__init__(self, t)

class IRQHubLayout(object):
    def __init__(self, hub, generator):
        leafs = [ dst for dst in hub.dsts ]
        while len(leafs) > 1:
            new_leafs = []
            while leafs:
                left = leafs.pop()
                if not leafs:
                    new_leafs.append(left)
                else:
                    right = leafs.pop()
                    new_leafs.append((left, right))
            leafs = new_leafs
        self.root = leafs[0]

        self.gen = generator
        self.hub = hub

    def _gen_irq_get(self, parent_name, node):
        if isinstance(node[0], DeviceNode):
            # leaf
            return ("", self.gen.gen_irq_get(node, parent_name))
        else:
            # inner node
            self.gen.use_type_name("qemu_irq_split")

            child1 = self.gen.gen_name_for_irq(node[0])
            child2 = self.gen.gen_name_for_irq(node[1])

            child1_code = self._gen_irq_get(child1, node[0])
            child2_code = self._gen_irq_get(child2, node[1])

            decl_code = "    qemu_irq %s;\n" % child1
            decl_code += "    qemu_irq %s;\n" % child2

            def_code =  """\
    {parent_name} = qemu_irq_split({child1}, {child2});
""".format(
    parent_name = parent_name,
    child1 = child1,
    child2 = child2
                    )
            return (child1_code[0] + child2_code[0] + decl_code,
                    child1_code[1] + child2_code[1] + def_code)

    def gen_irq_get(self):
        root_name = self.gen.gen_name_for_irq(self.hub)
        return self._gen_irq_get(root_name, self.root)

class MachineType(QOMType):

    def reset_generator(self):
        self.device_count = 0
        self.bus_count = 0
        self.irq_count = 0
        self.mem_count = 0
        self.node_map = {}
        self.init_used_types = []

    def use_type(self, t):
        if t in self.init_used_types:
            return
        self.init_used_types.append(t)

    def use_type_name(self, name):
        t = Type.lookup(name)
        self.use_type(t)

    def gen_name_for_device(self, node):
        if node in self.node_map.keys():
            return self.node_map[node]

        ret = "dev_%u" % self.device_count
        self.device_count += 1
        self.node_map[ret] = node
        self.node_map[node] = ret
        return ret

    def gen_name_for_bus(self, node):
        if node in self.node_map.keys():
            return self.node_map[node]

        ret = "bus_%u" % self.bus_count
        self.bus_count += 1
        self.node_map[ret] = node
        self.node_map[node] = ret
        return ret

    def gen_name_for_irq(self, node):
        if node in self.node_map.keys():
            return self.node_map[node]

        ret = "irq_%u" % self.irq_count
        self.irq_count += 1
        self.node_map[ret] = node
        self.node_map[node] = ret
        return ret

    def gen_name_for_mem(self, node):
        if node in self.node_map.keys():
            return self.node_map[node]

        ret = "mem_%u" % self.mem_count
        self.mem_count += 1
        self.node_map[ret] = node
        self.node_map[node] = ret
        return ret

    def gen_prop_val(self, prop):
        if isinstance(prop.prop_val, str) and Type.exists(prop.prop_val):
            self.use_type_name(prop.prop_val)
            return prop.prop_val
        if prop.prop_type == QOMPropertyTypeString:
            return "\"%s\"" % str(prop.prop_val)
        elif prop.prop_type == QOMPropertyTypeBoolean:
            if not isinstance(prop.prop_val, bool):
                raise IncorrectPropertyValue()

            self.use_type_name("bool")
            return "true" if prop.prop_val else "false"
        elif prop.prop_type == QOMPropertyTypeInteger:
            if not isinstance(prop.prop_val, int):
                raise IncorrectPropertyValue()

            return "0x%x" % prop.prop_val
        elif prop.prop_type == QOMPropertyTypeLink:
            if prop.prop_val is None:
                self.use_type_name("NULL")

                return "NULL"
            else:
                self.use_type_name("OBJECT")

                return "OBJECT(%s)" % self.node_map[prop.prop_val]
        else:
            raise UnknownPropertyType()

    def gen_irq_get(self, irq, var_name):
        self.use_type_name("DEVICE")

        if irq[2] is None:
            self.use_type_name("qdev_get_gpio_in")

            return """\
    {irq_name} = qdev_get_gpio_in(DEVICE({dst_name}), {dst_index});
""".format(
    irq_name = var_name,
    dst_name = self.gen_name_for_device(irq[0]),
    dst_index = irq[1],
            )

    def gen_irq_connect(self, irq, var_name):
        if irq[2] is None:
            self.use_type_name("DEVICE")
            self.use_type_name("qdev_connect_gpio_out")

            return """\
    qdev_connect_gpio_out(DEVICE({src_name}), {src_index}, {irq_name});
""".format(
    irq_name = var_name,
    src_name = self.gen_name_for_device(irq[0]),
    src_index = irq[1]
            )
        else:
            sysbus_name = Type.lookup("SYSBUS_DEVICE_GPIO_IRQ").text
            if sysbus_name == "\"%s\"" % irq[2] or "SYSBUS_DEVICE_GPIO_IRQ" == irq[2]:
                self.use_type_name("sysbus_connect_irq")
                self.use_type_name("SYS_BUS_DEVICE")

                return """\
    sysbus_connect_irq(SYS_BUS_DEVICE({src_name}), {src_index}, {irq_name});
""".format(
    irq_name = var_name,
    src_name = self.gen_name_for_device(irq[0]),
    src_index = irq[1]
                )
            else:
                self.use_type_name("DEVICE")
                self.use_type_name("qdev_connect_gpio_out_named")
                if Type.exists(irq[2]):
                    self.use_type_name(irq[2])

                return """\
    qdev_connect_gpio_out_named(DEVICE({src_name}), {gpio_name}, {src_index}, {irq_name});
""".format(
    irq_name = var_name,
    src_name = self.gen_name_for_device(irq[0]),
    src_index = irq[1],
    gpio_name = irq[2] if Type.exists(irq[2]) else "\"%s\"" % irq[2]
                )

    def __init__(self, machine):
        super(MachineType, self).__init__(machine.name)

        machine.link()

        self.name = machine.name

        # source file model
        source_path = \
            os.path.join("hw", machine.directory,
                         self.qtn.for_header_name + ".c")

        self.source = Source(source_path)

        all_nodes = list(machine.devices)
        all_nodes.extend(machine.buses)
        all_nodes.extend(machine.irqs)
        all_nodes.extend(machine.mems)
        all_nodes.extend(machine.irq_hubs)
        all_nodes = sort_topologically(all_nodes)

        decl_code = ""
        def_code = ""
        self.reset_generator()

        skip_nl = False

        for idx, node in enumerate(all_nodes):
            if not skip_nl:
                if idx > 0:
                    def_code += "\n"
            else:
                skip_nl = False

            if isinstance(node, DeviceNode):
                self.use_type_name("qdev_init_nofail")
                self.use_type_name("BUS")
                if Type.exists(node.qom_type):
                    self.use_type_name(node.qom_type)

                dev_name = self.gen_name_for_device(node)

                props_code = ""
                for p in node.properties:
                    self.use_type_name("OBJECT")
                    self.use_type_name(p.prop_type.set_f)
                    if Type.exists(p.prop_name):
                        self.use_type_name(p.prop_name)
                    if Type.exists(p.prop_val):
                        self.use_type_name(p.prop_val)

                    props_code += """
    {set_func}(OBJECT({dev_name}), {value}, {prop_name}, NULL);\
""".format(
    set_func = p.prop_type.set_f,
    dev_name = dev_name,
    prop_name = p.prop_name if Type.exists(p.prop_name) else "\"%s\"" % p.prop_name,
    value = self.gen_prop_val(p)
                        )

                if isinstance(node, PCIExpressDeviceNode):
                    self.use_type_name("PCIDevice")
                    self.use_type_name("pci_create_multifunction")
                    self.use_type_name("bool")
                    self.use_type_name("DEVICE")

                    decl_code += "    PCIDevice *%s;\n" % dev_name
                    def_code += """\
    {dev_name} = pci_create_multifunction({bus_name}, PCI_DEVFN({slot}, {func}), {multifunction}, {qom_type});{props_code}
    qdev_init_nofail(DEVICE({dev_name}));
""".format(
    dev_name = dev_name,
    bus_name = self.gen_name_for_bus(node.parent_bus),
    qom_type = node.qom_type if Type.exists(node.qom_type) else "\"%s\"" % node.qom_type,
    props_code = props_code,
    multifunction = "true" if node.multifunction else "false",
    slot = node.slot,
    func = node.function
                        )
                else:
                    self.use_type_name("DeviceState")
                    self.use_type_name("qdev_create")
    
                    decl_code += "    DeviceState *%s;\n" % dev_name
                    def_code += """\
    {dev_name} = qdev_create({bus_name}, {qom_type});{props_code}
    qdev_init_nofail({dev_name});
""".format(
    dev_name = dev_name,
    bus_name = "NULL" if (node.parent_bus is None ) or isinstance(node.parent_bus, SystemBusNode) else "BUS(%s)" % self.gen_name_for_bus(node.parent_bus),
    qom_type = node.qom_type if Type.exists(node.qom_type) else "\"%s\"" % node.qom_type,
    props_code = props_code
                        )

                if isinstance(node, SystemBusDeviceNode):
                    for idx, mmio in enumerate(node.mmio_mappings):
                        if mmio is not None:
                            self.use_type_name("sysbus_mmio_map")
                            self.use_type_name("SYS_BUS_DEVICE")

                            if isinstance(mmio, str) and Type.exists(mmio):
                                self.use_type_name(mmio)
                                mmio_val = str(mmio)
                            else:
                                mmio_val = "0x%x" % mmio

                            def_code += """\
    sysbus_mmio_map(SYS_BUS_DEVICE({dev_name}), {idx}, {mmio_val});
""".format(
    dev_name = dev_name,
    idx = idx,
    mmio_val = mmio_val
                    )

                for bus_idx, bus in enumerate(node.buses):
                    if len(bus.devices) == 0:
                        continue

                    bus_name = self.gen_name_for_bus(bus)
                    try:
                        if isinstance(bus, PCIExpressBusNode):
                            if isinstance(node, SystemBusDeviceNode):
                                bridge_cast = "PCI_HOST_BRIDGE"
                                bus_field = "bus"
                            elif isinstance(node, PCIExpressDeviceNode):
                                bridge_cast = "PCI_BRIDGE"
                                bus_field = "sec_bus"
                            else:
                                raise UnknownBusBridgeType(node.parent_bus, bus)

                            self.use_type_name(bridge_cast)

                            def_code += """\
    {bus_name} = {bridge_cast}({bridge_name})->{bus_field};
""".format(
    bus_name = bus_name,
    bridge_name = dev_name,
    bridge_cast = bridge_cast,
    bus_field = bus_field
                                )
                        else:
                            raise UnknownBusBridgeType(node.parent_bus, bus)
                    except UnknownBusBridgeType:
                        self.use_type_name("qdev_get_child_bus")
                        self.use_type_name("DEVICE")
                        if bus.cast is not None:
                            self.use_type_name(bus.cast)

                        def_code += """\
    {bus_name} = {bus_cast};
""".format(
    bus_name = bus_name,
    bus_cast = ("(%s *) %%s" % bus.c_type) if bus.cast is None else ("%s(%%s)" % bus.cast),
                            ) % """\
qdev_get_child_bus(DEVICE({bridge_name}), "{bus_child_name}")\
""".format(
    bridge_name = dev_name,
    bus_child_name = bus.child_name if len(node.buses) == 1 and not bus.force_index else "%s.%u" % (bus.child_name, bus_idx),
                            )

            elif isinstance(node, BusNode):
                # No definition code will be generated
                skip_nl = True

                if isinstance(node, SystemBusNode):
                    continue
                if len(node.devices) == 0:
                    continue

                self.use_type_name(node.c_type)

                bus_name = self.gen_name_for_bus(node)

                decl_code += "    %s *%s;\n" % (node.c_type, bus_name)
            elif isinstance(node, IRQLine):
                self.use_type_name("qemu_irq")

                irq_name = self.gen_name_for_irq(node)

                decl_code += "    qemu_irq %s;\n" % irq_name

                def_code += self.gen_irq_get(node.dst, irq_name) \
                          + self.gen_irq_connect(node.src, irq_name)
            elif isinstance(node, MemoryNode):
                self.use_type_name("MemoryRegion")
                if Type.exists(node.size):
                    self.use_type_name(node.size)
                if Type.exists(node.name):
                    self.use_type_name(node.name)

                mem_name = self.gen_name_for_mem(node)

                decl_code += "    MemoryRegion *%s;\n" % mem_name

                def_code += "    %s = g_new(MemoryRegion, 1);\n" % mem_name

                if isinstance(node, MemoryAliasNode):
                    self.use_type_name("memory_region_init_alias")
                    if Type.exists(node.alias_offset):
                        self.use_type_name(node.alias_offset)

                    def_code += """\
    memory_region_init_alias({mem_name}, NULL, {dbg_name}, {orig}, {offset}, {size});
""".format(
    mem_name = mem_name, 
    dbg_name = node.name if Type.exists(node.name) else "\"%s\"" % node.name,
    size = node.size,
    orig = self.gen_name_for_mem(node.alias_to),
    offset = node.alias_offset
                    )
                elif    isinstance(node, MemoryRAMNode) \
                     or isinstance(node, MemoryROMNode) :
                    self.use_type_name("memory_region_init_ram")
                    self.use_type_name("vmstate_register_ram_global")

                    def_code += """\
    memory_region_init_ram({mem_name}, NULL, {dbg_name}, {size}, NULL);
    vmstate_register_ram_global({mem_name});
""".format(
    mem_name = mem_name,
    dbg_name = node.name if Type.exists(node.name) else "\"%s\"" % node.name,
    size = node.size
                    )
                else:
                    self.use_type_name("memory_region_init")

                    def_code += """\
    memory_region_init({mem_name}, NULL, {dbg_name}, {size});
""".format(
    mem_name = mem_name,
    dbg_name = node.name if Type.exists(node.name) else "\"%s\"" % node.name,
    size = node.size
                    )

                if node.parent is not None:
                    if      isinstance(node.offset, str) \
                        and Type.exists(node.offset):
                        self.use_type_name(node.offset)
                    if node.may_overlap:
                        self.use_type_name("memory_region_add_subregion_overlap")
                        if      isinstance(node.priority, str) \
                            and Type.exists(node.priority):
                            self.use_type_name(node.priority)

                        def_code += """\
    memory_region_add_subregion_overlap({parent_name}, {offset}, {child}, {priority});
""".format(
    parent_name = self.node_map[node.parent],
    offset = node.offset,
    priority = node.priority,
    child = mem_name
                            )
                    else:
                        self.use_type_name("memory_region_add_subregion")
                        if      isinstance(node.priority, str) \
                            and Type.exists(node.priority):
                            self.use_type_name(node.priority)

                        def_code += """\
    memory_region_add_subregion({parent_name}, {offset}, {child});
""".format(
    parent_name = self.node_map[node.parent],
    offset = node.offset,
    child = mem_name
                            )

            elif isinstance(node, IRQHub):
                self.use_type_name("qemu_irq")

                hub_in_name = self.gen_name_for_irq(node)

                decl_code += "    qemu_irq %s;\n" % hub_in_name

                hubl = IRQHubLayout(node, self)

                code = hubl.gen_irq_get()
                decl_code += code[0]
                def_code += code[1]

                for src in node.srcs:
                    def_code += self.gen_irq_connect(src, hub_in_name)
            else:
                raise UnknownMachineNodeType(str(type(node)))

        # machine initialization function
        self.instance_init = Function(
            name = "init_%s" % self.qtn.for_id_name,
            static = True,
            args = [
                Type.lookup("MachineState").gen_var("machine", pointer = True)
                ],
            body = decl_code + "\n" + def_code,
            used_types = self.init_used_types
            )
        self.source.add_type(self.instance_init)

        # machine class definition function
        self.class_init = Function(
            name = "machine_%s_class_init" % self.qtn.for_id_name,
            static = True,
            ret_type = Type.lookup("void"),
            args = [
                Type.lookup("ObjectClass").gen_var("oc", pointer = True),
                Type.lookup("void").gen_var("opaque", pointer = True)
                ],
            body = """\
    MachineClass *mc = MACHINE_CLASS(oc);

    mc->name = \"{type_name}\";
    mc->desc = \"{desc}\";
    mc->init = {instance_init};
""".format(
    type_name = self.qtn.for_id_name,
    desc = self.name,
    instance_init = self.instance_init.name
                ),
            used_types = [
                    Type.lookup("MachineClass"),
                    Type.lookup("MACHINE_CLASS"),
                    self.instance_init
                ]
            )
        self.source.add_type(self.class_init)

        # machine type definition structure
        type_machine_macro = Type.lookup("TYPE_MACHINE") 
        type_machine_suf_macro = Type.lookup("TYPE_MACHINE_SUFFIX")

        self.type_info = Type.lookup("TypeInfo").gen_var(
            name = "machine_type_%s" % self.qtn.for_id_name,
            static = True,
            initializer = Initializer(
                code = """{{
    .name = \"{id}\" {suf},
    .parent = {parent},
    .class_init = {class_init}
}}""".format(
                id = self.qtn.for_id_name,
                suf = type_machine_suf_macro.name,
                parent = type_machine_macro.name,
                class_init = self.class_init.name
                ),
            used_types = [
                type_machine_suf_macro,
                type_machine_macro,
                self.class_init
                ]
                )
            )
        self.source.add_global_variable(self.type_info)

        # machine type registration function
        self.type_reg_func = Function(
            name = "machine_init_%s" % self.qtn.for_id_name,
            body = """\
    type_register(&{type_info});
""".format(
    type_info = self.type_info.name
                ),
            static = True,
            used_types = [Type.lookup("type_register")],
            used_globals = [self.type_info]
            )
        self.source.add_type(self.type_reg_func)

        # Main machine registration macro
        machine_init_def = Type.lookup("machine_init").gen_var()
        machine_init_def_args = Initializer(
            code = {"function": self.type_reg_func.name},
            used_types = [self.type_reg_func]
            )
        self.source.add_usage(machine_init_def.gen_usage(machine_init_def_args))

    def generate_source(self):
        return self.source.generate()
