from pade.core.agent import Agent
from pade.acl.aid import AID
from pade.acl.filters import Filter
from pade.behaviours.protocols import FipaSubscribeProtocol, FipaRequestProtocol
from pade.misc.utility import display_message

class SubscribeProtocol(FipaSubscribeProtocol):

    def __init__(self, agent):
        super(SubscribeProtocol, self).__init__(agent, message=None, is_initiator=False)

    def handle_subscribe(self, message):
        super(SubscribeProtocol, self).handle_subscribe(message)
        sender = AID(message.sender.aid)
        self.register(sender)

    def handle_cancel(self, message):
        super(SubscribeProtocol, self).handle_cancel(message)
        sender = AID(message.sender.aid)
        self.deregister(sender)

class RequestRegistration(FipaRequestProtocol):

    def __init__(self, message=None, is_initiator=False):
        super(RequestRegistration, self).__init__(self, message, is_initiator)
        self.filter_register = Filter()
        self.filter_register.set_convwersation_id

    def handle_request(self, message):
        super(RequestRegistration, self).handle_request(message)
        sender = AID(message.sender.aid)
        
        self.agent.registry[sender.getName()] = 

class DirectoryFacilitator(Agent):

    def __init__(self, host='localhost', port=8002, debug=False):
        self.df_aid = AID('df@' + str(host) + ':' + str(port))
        super(DirectoryFacilitator, self).__init__(self.df_aid, debug=debug)

        self.registry = {}

        self.behaviours = [
            SubscribeProtocol(self)
        ]

        