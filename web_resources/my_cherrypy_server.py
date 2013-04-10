import os
import cherrypy

PATH = os.path.abspath(os.path.dirname(__file__))
class Root(object): pass

cherrypy.server.socket_port = 8000
cherrypy.server.socket_host = '0.0.0.0'

cherrypy.tree.mount(Root(), '/', config={
        '/': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': PATH,
                'tools.staticdir.index': 'predDB.html',
            },
    })

# cherrypy.quickstart()
cherrypy.engine.start()
cherrypy.engine.block()
