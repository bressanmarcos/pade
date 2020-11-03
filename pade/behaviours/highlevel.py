from typing import Any, Callable

from pade.acl.messages import ACLMessage
from pade.behaviours.protocols import \
    FipaRequestProtocol as _FipaRequestProtocol
from pade.core.agent import ImprovedAgent


class FipaProtocolComplete(Exception):
    """General handler to signal protocol completion"""


class FipaMessageHandler(Exception):
    """General handler for FIPA messages"""

    def __init__(self, message: ACLMessage):
        self.message = message
        super().__init__(message)


class FipaAgreeHandler(FipaMessageHandler):
    """Exception handler for FIPA-AGREE messages"""


class FipaRefuseHandler(FipaMessageHandler):
    """Exception handler for FIPA-REFUSE messages"""


class FipaInformHandler(FipaMessageHandler):
    """Exception handler for FIPA-INFORM messages"""


class FipaFailureHandler(FipaMessageHandler):
    """Exception handler for FIPA-FAILURE messages"""


class FipaRequestProtocolInitiator(_FipaRequestProtocol):

    def __init__(self, agent):
        _FipaRequestProtocol.__init__(
            self, agent, message=None, is_initiator=True)

        # Denote each open request. It is possible to have multiple
        # sessions with a same party.
        # The pair (participant_aid, conversation_id) represents a unique session.
        self.open_sessions = {}

    def execute(self, message: ACLMessage):
        """Called whenever the agent receives a message.
        The message was NOT yet filtered in terms of:
        protocol, conversation_id or performative."""
        super(FipaRequestProtocolInitiator, self).execute(message)

        # Filter for protocol
        if not message.protocol == ACLMessage.FIPA_REQUEST_PROTOCOL:
            return

        # Filter for session_id (participant_aid, conversation_id)
        session_id = (message.sender, message.conversation_id)
        if session_id not in self.open_sessions:
            return

        # Resume generator
        generator = self.open_sessions[session_id]
        handlers = {
            ACLMessage.INFORM: lambda: generator.send(message),
            ACLMessage.AGREE: lambda: generator.throw(FipaAgreeHandler, message),
            ACLMessage.REFUSE: lambda: generator.throw(FipaRefuseHandler, message),
            ACLMessage.FAILURE: lambda: generator.throw(
                FipaFailureHandler, message)
        }
        try:
            handlers[message.performative]()
        except (StopIteration, FipaMessageHandler):
            pass
        except KeyError:
            return

        # Clear session if final message was received
        if message.performative in (ACLMessage.REFUSE, ACLMessage.INFORM, ACLMessage.FAILURE):
            self.delete_session(session_id)

    def delete_session(self, session_id):
        """Delete an open session and terminate protocol session"""

        try:
            generator = self.open_sessions.pop(session_id)
        except KeyError:
            pass
        else:
            if sum(1 for s_id in self.open_sessions if s_id[1] == session_id[1]) == 0:
                # Signal protocol completion if it's the last message
                try:
                    generator.throw(FipaProtocolComplete)
                except (StopIteration, FipaProtocolComplete):
                    pass

    def send_request(self, message: ACLMessage):

        message.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)
        message.set_performative(ACLMessage.REQUEST)

        # Send message to all receivers
        self.agent.send_until(message)

        return message

    def run(self, generator) -> None:
        """Register generator before sending message."""
        message = next(generator)

        # Register generator in session
        for receiver in message.receivers:
            session_id = (receiver, message.conversation_id)
            self.open_sessions[session_id] = generator
            # The session expires in 5 minutes by default
            self.agent.call_later(300, lambda: self.delete_session(session_id))


class FipaRequestProtocolParticipant(_FipaRequestProtocol):

    def __init__(self, agent):
        _FipaRequestProtocol.__init__(
            self, agent, message=None, is_initiator=False)
        self.callbacks = []

    def execute(self, message: ACLMessage):
        """Called whenever the agent receives a message.
        The message was NOT yet filtered in terms of:
        protocol, conversation_id or performative."""
        super(FipaRequestProtocolParticipant, self).execute(message)

        # Filter for protocol
        if not message.protocol == ACLMessage.FIPA_REQUEST_PROTOCOL:
            return

        # Filter for performative
        if not message.performative == ACLMessage.REQUEST:
            return

        for callback in self.callbacks:
            callback(message)

    def add_callback(self, callback: Callable[[ACLMessage], Any]):
        """Add function to be called for request"""
        self.callbacks.append(callback)

    def send_inform(self, message: ACLMessage):

        message.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)
        message.set_performative(ACLMessage.INFORM)

        # Send message to all receivers
        self.agent.send_until(message)

        return message

    def send_failure(self, message: ACLMessage):

        message.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)
        message.set_performative(ACLMessage.FAILURE)

        # Send message to all receivers
        self.agent.send_until(message)

        return message

    def send_agree(self, message: ACLMessage):

        message.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)
        message.set_performative(ACLMessage.AGREE)

        # Send message to all receivers
        self.agent.send_until(message)

        return message

    def send_refuse(self, message: ACLMessage):

        message.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)
        message.set_performative(ACLMessage.REFUSE)

        # Send message to all receivers
        self.agent.send_until(message)

        return message


def FipaRequestProtocol(agent: ImprovedAgent, is_initiator=True):

    if is_initiator:
        instance = FipaRequestProtocolInitiator(agent)
    else:
        instance = FipaRequestProtocolParticipant(agent)

    agent.behaviours.append(instance)
    return instance
