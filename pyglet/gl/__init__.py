# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2019 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

"""OpenGL and GLU interface.

This package imports all OpenGL, GLU and registered OpenGL extension
functions.  Functions have identical signatures to their C counterparts.

OpenGL is documented in full at the `OpenGL Reference Pages`_.

The `OpenGL Programming Guide`_, also known as "The Red Book", is a popular
reference manual organised by topic. It is available in digital and paper
editions.

.. _OpenGL Reference Pages: https://www.khronos.org/registry/OpenGL-Refpages/
.. _OpenGL Programming Guide: http://opengl-redbook.com/

The following subpackages are imported into this "mega" package already
(and so are available by importing ``pyglet.gl``):

``pyglet.gl.gl``
    OpenGL
``pyglet.gl.glu``
    GLU
``pyglet.gl.gl.glext_arb``
    ARB registered OpenGL extension functions

These subpackages are also available, but are not imported into this namespace
by default:

``pyglet.gl.glext_nv``
    nVidia OpenGL extension functions
``pyglet.gl.agl``
    AGL (Mac OS X OpenGL context functions)
``pyglet.gl.glx``
    GLX (Linux OpenGL context functions)
``pyglet.gl.glxext_arb``
    ARB registered GLX extension functions
``pyglet.gl.glxext_nv``
    nvidia GLX extension functions
``pyglet.gl.wgl``
    WGL (Windows OpenGL context functions)
``pyglet.gl.wglext_arb``
    ARB registered WGL extension functions
``pyglet.gl.wglext_nv``
    nvidia WGL extension functions

The information modules are provided for convenience, and are documented below.
"""
import pyglet as _pyglet

from pyglet.gl.lib import GLException
from pyglet.gl.gl import *
from pyglet.gl.glu import *
from pyglet.gl.glext_arb import *
from pyglet.gl import gl_info

from pyglet import compat_platform
from .base import ObjectSpace, CanvasConfig, Context

import sys as _sys
_is_pyglet_doc_run = hasattr(_sys, "is_pyglet_doc_run") and _sys.is_pyglet_doc_run

#: The active OpenGL context.
#:
#: You can change the current context by calling `Context.set_current`;
#: do not modify this global.
#:
#: :type: `Context`
#:
#: .. versionadded:: 1.1
current_context = None


class ContextException(Exception):
    pass


class ConfigException(Exception):
    pass


if _pyglet.options['debug_texture']:
    _debug_texture_total = 0
    _debug_texture_sizes = {}
    _debug_texture = None


    def _debug_texture_alloc(texture, size):
        global _debug_texture_total

        _debug_texture_sizes[texture] = size
        _debug_texture_total += size

        print('%d (+%d)' % (_debug_texture_total, size))


    def _debug_texture_dealloc(texture):
        global _debug_texture_total

        size = _debug_texture_sizes[texture]
        del _debug_texture_sizes[texture]
        _debug_texture_total -= size

        print('%d (-%d)' % (_debug_texture_total, size))


    _glBindTexture = glBindTexture


    def glBindTexture(target, texture):
        global _debug_texture
        _debug_texture = texture
        return _glBindTexture(target, texture)


    _glTexImage2D = glTexImage2D


    def glTexImage2D(target, level, internalformat, width, height, border,
                     format, type, pixels):
        try:
            _debug_texture_dealloc(_debug_texture)
        except KeyError:
            pass

        if internalformat in (1, GL_ALPHA, GL_INTENSITY, GL_LUMINANCE):
            depth = 1
        elif internalformat in (2, GL_RGB16, GL_RGBA16):
            depth = 2
        elif internalformat in (3, GL_RGB):
            depth = 3
        else:
            depth = 4  # Pretty crap assumption
        size = (width + 2 * border) * (height + 2 * border) * depth
        _debug_texture_alloc(_debug_texture, size)

        return _glTexImage2D(target, level, internalformat, width, height,
                             border, format, type, pixels)


    _glDeleteTextures = glDeleteTextures


    def glDeleteTextures(n, textures):
        if not hasattr(textures, '__len__'):
            _debug_texture_dealloc(textures.value)
        else:
            for i in range(n):
                _debug_texture_dealloc(textures[i].value)

        return _glDeleteTextures(n, textures)


def _create_shadow_window():
    global _shadow_window

    import pyglet
    if not pyglet.options['shadow_window'] or _is_pyglet_doc_run:
        return

    from pyglet.window import Window
    _shadow_window = Window(width=1, height=1, visible=False)
    _shadow_window.switch_to()

    from pyglet import app
    app.windows.remove(_shadow_window)


if _is_pyglet_doc_run:
    from .base import Config
elif compat_platform in ('win32', 'cygwin'):
    from .win32 import Win32Config as Config
elif compat_platform.startswith('linux'):
    from .xlib import XlibConfig as Config
elif compat_platform == 'darwin':
    from .cocoa import CocoaConfig as Config
del base  # noqa: F821


# XXX remove
_shadow_window = None

# Import pyglet.window now if it isn't currently being imported (this creates
# the shadow window).
if not _is_pyglet_doc_run and 'pyglet.window' not in _sys.modules and _pyglet.options['shadow_window']:
    # trickery is for circular import 
    _pyglet.gl = _sys.modules[__name__]
    import pyglet.window
