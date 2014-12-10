"""
Copyright 2006, 2007, 2014 Free Software Foundation, Inc.
This file is part of GNU Radio

GNU Radio Companion is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

GNU Radio Companion is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""

from functools import wraps

from runtime_swig import hier_block2_swig, dot_graph
import pmt


def _multiple_endpoints(func):
    def coerce_endpoint(endp, default_port=0):
        if hasattr(endp, 'to_basic_block'):
            return endp.to_basic_block(), default_port
        try:
            block, port = endp
            return block.to_basic_block(), port
        except ValueError:
            raise ValueError("unable to coerce endpoint")
    @wraps(func)
    def wrapped(self, *points):
        if not points:
            raise ValueError("At least one endpoint required for " + func.__name__)
        elif len(points) == 1:
            func(points[0].to_basic_block())
        else:
            for src, dst in map(lambda i: points[i:i + 2], range(len(points) - 1)):
                func(self, *(coerce_endpoint(src) + coerce_endpoint(dst)))
    return wrapped


def _optional_endpoints(func):
    @wraps(func)
    def wrapped(self, src, srcport, dst=None, dstport=None):
        if dst is None and dstport is None:
            (src, srcport), (dst, dstport) = src, srcport
        return func(self,
                    src.to_basic_block(), srcport,
                    dst.to_basic_block(), dstport)
    return wrapped


# This makes a 'has-a' relationship to look like an 'is-a' one.
#
# It allows Python classes to subclass this one, while passing through
# method calls to the C++ class shared pointer from SWIG.
#
# It also allows us to intercept method calls if needed
#
class hier_block2(object):
    """
    Subclass this to create a python hierarchical block.

    This is a python wrapper around the C++ hierarchical block implementation.
    Provides convenience functions and allows proper Python subclassing.
    """

    def __init__(self, name, input_signature, output_signature):
        """
        Create a hierarchical block with a given name and I/O signatures.
        """
        self._impl = hier_block2_swig(name, input_signature, output_signature)

    def __getattr__(self, name):
        """
        Pass-through member requests to the C++ object.
        """
        if not hasattr(self, "_impl"):
            raise RuntimeError(
                "{0}: invalid state -- did you forget to call {0}.__init__ in "
                "a derived class?".format(self.__class__.__name__))
        return getattr(self._impl, name)

    # FIXME: these should really be implemented
    # in the original C++ class (gr_hier_block2), then they would all be inherited here

    @_multiple_endpoints
    def connect(self, *args):
        """
        Connect two or more block endpoints.  An endpoint is either a (block, port)
        tuple or a block instance.  In the latter case, the port number is assumed
        to be zero.

        To connect the hierarchical block external inputs or outputs to internal block
        inputs or outputs, use 'self' in the connect call.

        If multiple arguments are provided, connect will attempt to wire them in series,
        interpreting the endpoints as inputs or outputs as appropriate.
        """
        self.primitive_connect(*args)

    @_multiple_endpoints
    def disconnect(self, *args):
        """
        Disconnect two or more endpoints in the flowgraph.

        To disconnect the hierarchical block external inputs or outputs to internal block
        inputs or outputs, use 'self' in the connect call.

        If more than two arguments are provided, they are disconnected successively.
        """
        self.primitive_disconnect(*args)

    @_optional_endpoints
    def msg_connect(self, *args):
        """
        Connect two message ports in the flowgraph.

        If only two arguments are provided, they must be endpoints (block, port)
        """
        self.primitive_msg_connect(*args)

    @_optional_endpoints
    def msg_disconnect(self, *args):
        """
        Disconnect two message ports in the flowgraph.

        If only two arguments are provided, they must be endpoints (block, port)
        """
        self.primitive_msg_disconnect(*args)

    def message_port_register_hier_in(self, portname):
        """
        Register a message port for this hier block
        """
        self.primitive_message_port_register_hier_in(pmt.intern(portname))

    def message_port_register_hier_out(self, portname):
        """
        Register a message port for this hier block
        """
        self.primitive_message_port_register_hier_out(pmt.intern(portname))

    def dot_graph(self):
        """
        Return graph representation in dot language
        """
        return dot_graph(self._impl)
