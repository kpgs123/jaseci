"""
Main master handler for each user of Jaseci, serves as main interface between
between user and Jaseci
"""
import base64
import uuid
from inspect import signature
from inspect import getdoc
from jaseci.element import element
from jaseci.graph.graph import graph
from jaseci.graph.node import node
from jaseci.actor.sentinel import sentinel
from jaseci.actor.walker import walker
from jaseci.utils.id_list import id_list
from jaseci.utils.utils import logger
from jaseci.api.legacy import legacy_api
from jaseci.api.alias import alias_api


class master(element, legacy_api, alias_api):
    """Main class for master functions for user"""

    def __init__(self, email="Anonymous", *args, **kwargs):
        self.graph_ids = id_list(self)
        self.sentinel_ids = id_list(self)
        element.__init__(self, name=email,
                         kind="Jaseci Master", *args, **kwargs)
        alias_api.__init__(self)

    def api_create_graph(self, name: str):
        """
        Create a graph instance and return root node graph object
        """
        gph = graph(h=self._h, name=name)
        self.graph_ids.add_obj(gph)
        return gph.serialize()

    def api_create_sentinel(self, name: str):
        """
        Create blank sentinel and return object
        """
        snt = sentinel(h=self._h, name=name, code='# Jac Code')
        self.sentinel_ids.add_obj(snt)
        return snt.serialize()

    def api_list_graph(self, detailed: bool = False):
        """
        Provide complete list of all graph objects (list of root node objects)
        """
        gphs = []
        for i in self.graph_ids.obj_list():
            gphs.append(i.serialize(detailed=detailed))
        return gphs

    def api_list_walker(self, snt: sentinel, detailed: bool = False):
        """
        List walkers known to sentinel
        """
        walks = []
        for i in snt.walker_ids.obj_list():
            walks.append(i.serialize(detailed=detailed))
        return walks

    def api_list_sentinel(self, detailed: bool = False):
        """
        Provide complete list of all sentinel objects
        """
        snts = []
        for i in self.sentinel_ids.obj_list():
            snts.append(i.serialize(detailed=detailed))
        return snts

    def api_delete_graph(self, gph: graph):
        """
        Permanently delete graph with given id
        """
        self.graph_ids.destroy_obj(gph)
        return [f'Graph {gph.id} successfully deleted']

    def api_delete_sentinel(self, snt: sentinel):
        """
        Permanently delete sentinel with given id
        """
        self.sentinel_ids.destroy_obj(snt)
        return [f'Sentinel {snt.id} successfully deleted']

    def api_get_graph(self, gph: graph, detailed: bool = False,
                      dot: bool = False):
        """
        Return the content of the graph
        """
        if(dot):
            return gph.graph_dot_str()
        else:
            nds = []
            for i in gph.get_network_nodes():
                nds.append(i.serialize(detailed=detailed))
            return nds

    def api_get_object(self, obj: element, detailed: bool = False):
        """
        Return the content of the graph
        """
        return obj.serialize(detailed=detailed)

    def api_get_jac(self, snt: sentinel):
        """
        Get sentinel implementation in form of Jac source code
        """
        return [snt.code]

    def api_set_jac(self, snt: sentinel, code: str, encoded: bool):
        """
        Set sentinel implementation with Jac source code
        """
        if (encoded):
            try:
                code = base64.b64decode(code).decode()
            except UnicodeDecodeError:
                logger.error(
                    f'Code encoding invalid for Sentinel {snt.id}!')
                return [f'Code encoding invalid for Sentinel {snt.id}!']
        if (snt.code == code and snt.is_active):
            return [f'Sentinel {snt.id} already registered and active!']
        else:
            snt.code = code
            snt.register_code()
            snt.save()
            if(snt.is_active):
                return [f'Sentinel {snt.id} registered and active!']
            else:
                return [f'Sentinel {snt.id} code issues encountered!']

    def api_spawn_walker(self, snt: sentinel, name: str):
        """
        Creates new instance of walker and returns new walker object
        """
        wlk = snt.spawn(name)
        if(wlk):
            return wlk.serialize()
        else:
            return [f'Walker not found!']

    def api_unspawn(self, wlk: walker):
        """
        Delete instance of walker (not implemented yet)
        """

        return []

    def api_run(self, snt: sentinel, name: str,
                nd: node, ctx: dict = {}):
        """
        Creates walker instance, primes walker on node, executes walker,
        reports results, and cleans up walker instance.
        """
        wlk = snt.spawn(name)
        if(not wlk):
            return [f'Walker {name} not found!']
        wlk.prime(nd, prime_ctx=ctx)
        res = self.api_run_walker(wlk)
        wlk.destroy()
        return res

    def api_get_node_context(self, nd: node, ctx: list):
        """
        Returns value a given node
        """
        ret = {}
        nd_ctx = nd.serialize(detailed=True)['context']
        if(ctx):
            for i in nd_ctx.keys():
                if i in ctx:
                    ret[i] = nd_ctx[i]
        return ret

    def api_set_node_context(self, snt: sentinel, nd: node, ctx: dict):
        """
        Assigns values to member variables of a given node using ctx object
        """
        nd.set_context(
            ctx=ctx, arch=snt.arch_ids.get_obj_by_name('node.'+nd.kind).run())
        return nd.serialize()

    def destroy(self):
        """
        Destroys self from memory and persistent storage
        """
        for i in self.sentinel_ids.obj_list() + self.graph_ids.obj_list():
            i.destroy()
        super().destroy()

    def general_interface_to_api(self, params, api_name):
        """
        A mapper utility to interface to master class
        Assumptions:
            params is a dictionary of parameter names and values in UUID
            api_name is the name of the api being mapped to
        """
        param_map = {}
        if (not hasattr(self, api_name)):
            logger.error(f'{api_name} not a valid API')
            return False
        func_sig = signature(getattr(self, api_name))
        for i in func_sig.parameters.keys():
            if (i == 'self'):
                continue
            p_name = i
            p_type = func_sig.parameters[i].annotation
            p_default = func_sig.parameters[i].default
            param_map[i] = p_default if p_default is not \
                func_sig.parameters[i].empty else None
            if (p_name in params.keys()):
                val = params[p_name]
                if(str(val) in self.alias_map.keys()):
                    val = self.alias_map[val]
                if (issubclass(p_type, element)):
                    val = self._h.get_obj(uuid.UUID(val))
                    if (isinstance(val, p_type)):
                        param_map[i] = val
                    else:
                        logger.error(f'{type(val)} is not {p_type}')
                        param_map[i] = None
                else:  # TODO: Can do type checks here too
                    param_map[i] = val

            if (param_map[i] is None):
                logger.error(f'Invalid API parameter set - {params}')
                return False
        if (len(param_map) < len(params)-1):
            logger.warning(
                str(f'Unused parameters in API call - '
                    f'got {params.keys()}, expected {param_map.keys()}'))
        return getattr(self, api_name)(**param_map)

    def get_api_signature(self, api_name):
        """
        Checks for valid api name and returns signature
        """
        if (not hasattr(self, api_name)):
            logger.error(f'{api_name} not a valid API')
            return False
        else:
            return signature(getattr(master, api_name))

    def get_api_doc(self, api_name):
        """
        Checks for valid api name and returns signature
        """
        if (not hasattr(self, api_name)):
            logger.error(f'{api_name} not a valid API')
            return False
        else:
            return getdoc(getattr(master, api_name))