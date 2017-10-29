from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage
import core
import cherrypy

WebSocketPlugin(cherrypy.engine).subscribe()
cherrypy.tools.websocket = WebSocketTool()


class ChatWebSocketHandler(WebSocket):

    def __init__(self, *args, **kwargs):
        WebSocket.__init__(self, *args, **kwargs)
        core.WS_CLIENTS.add(self)

    @cherrypy.tools.json_in()
    def received_message(self, msg):
        self.send('THIS IS A RESPONSE')

    def closed(self, code, reason="A client left the room without a proper explanation."):
        core.WS_CLIENTS.remove(self)
        cherrypy.engine.publish('websocket-broadcast', TextMessage(reason))
