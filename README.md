# Python Agent DEvelopment framework (PADE)

This is a fork of the original PADE repository, flavoured with my particular conception choices.

It is intended to provide a more flexible interface, abstracting formalisms brought by FIPA standards (such as Interaction protocols) and providing tools that reduce language verbosity.

It is also a trampoline for ideas that may eventually be suggested as pull request for the original project.

Please support the [official release](https://github.com/grei-ufc/pade)!

<br>
<p align="center">
    <img src="https://raw.githubusercontent.com/lucassm/Pade/master/pade/images/pade_logo.png" alt="PADE" width="200">
</p>


The original README is available at (https://github.com/grei-ufc/pade).
The instructions below are complementary to the official project, and detail specifications for this fork.

## Main characteristics

- New `ImprovedAgent` class leverages the common `Agent` methods. I didn't want to modify directly the `Agent` class in order to separate functions necessary to components exclusive of this fork.

- Message content MUST be text strings or `ElementTree.Element` objects. Python primitives such as lists and dictionaries can be converted into JSON before being sent. Any binary data must be encoded in text beforehand (Base64 encoding is a way). An exception to this are `ElementTree.Element` objects, since they are directly embedded into ACLMessage XML envelopes. This works like so to get closer and closer to FIPA standards in order to ensure interoperability between different platforms.

- Asynchronous communication between agents still relies on `twisted` TCP sockets, but FIPA interaction protocols are managed to correspond to behavioral expectations described on FIPA standards. This takes the programmer from the task of manually following FIPA protocols and makes them focus on what really matters: the code;

- Interaction protocols provide a `run` method, intended to span and manage multiple sessions at the side of the initiator agent for each executed request. The `run` method receives a generator that yields right after sending an initiating message and creating a session;

- A session is identified by a pair (`participant aid`, `message correlation id`). It is created when an initiating send message is sent (`request`, `subscribe`, `cfp`) and deleted when the protocol is terminated (last message received, subscription cancelled, and so on). A session redirects received messages to its respective generator, resuming the calling process where it was paused / "yielded". The following code depicts the process to send a request:

```python
class AnAgent(ImprovedAgent):
    def __init__(self):
        self.request = FipaRequestProtocol(self, is_initiator=True)
        # `self.request` is also automatically added to `self.behaviours` to
        # avoid verbosity
    def make_request(receiver_aid):
        def async_request():
            message = ACLMessage()
            message.add_receiver(receiver_aid)
            message.set_content('Hello')
            # Send message and create a session
            self.request.send_request(message)
            while True:
                try:
                    # Request message must be `yield'ed`
                    response = yield message
                    # ... Treat `INFORM` type response
                except FipaFailureHandler as e:
                    response = e.message
                    # ... Treat `FAILURE` type response
                # ... other excepts ...
                except FipaProtocolComplete:
                    # End of protocol, break loop
                    break
            # Code after protocol end
        # Launch async request
        self.request.run(async_request())
```
