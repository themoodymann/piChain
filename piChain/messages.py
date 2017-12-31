"""This module defines the representation of all objects that need to be sent over the network and thus need to be
serialized and unserialized."""

import json
import jsonpickle


class PaxosMessage:
    """ A paxos message used to commit a block.

    Args:
        msg_type (str): TRY, TRY_OK, PROPOSE, PROPOSE_ACK or COMMIT.
        request_seq (int): each message contains a request sequence number s.t outdated messaged can be detected.

    Attributes:
        new_block (int): block_id of new block (block a quick node wants to commit).
        prop_block (int): block_id of proposed block.
        supp_block (int): block_id of support block (supporting the proposed block).
        com_block (int): block_id of compromise block.
        last_committed_block (int): block_id of last committed block (for faster recovery in case of partition).
    """
    def __init__(self, msg_type, request_seq):
        self.msg_type = msg_type  #
        self.request_seq = request_seq

        # content variables: are assigned depending on message type
        self.new_block = None
        self.prop_block = None
        self.supp_block = None
        self.com_block = None
        self.last_committed_block = None

    def serialize(self):
        """
        Returns (bytes): bytes representing the object.
        """
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'PAM', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        """
        Args:
            msg (json formatted str): PaxosMessage represented as a json formatted str.

        Returns (PaxosMessage): original PaxosMessage instance.
        """
        pam = jsonpickle.decode(msg['obj_str'])
        return pam


class RequestBlockMessage:
    """"Is sent if a node is missing a block.

    Args:
        block_id (int): block id of missing block.
    """
    def __init__(self, block_id):
        self.block_id = block_id

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'RQB', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        rqb = jsonpickle.decode(msg['obj_str'])
        return rqb


class RespondBlockMessage:
    """Is sent as a response to a `RequestBlockMessage`.

    Args:
        blocks (list): list containing the missing blocks.
    """
    def __init__(self, blocks):
        self.blocks = blocks  # the last 5 blocks starting from block the node misses

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'RSB', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        rsb = jsonpickle.decode(msg['obj_str'])
        return rsb


class AckCommitMessage:
    """Is broadcast once a node commits a block to perform genesis block change once all nodes committed a block.

    Args:
        block_id (int): block id of committed block.
    """
    def __init__(self, block_id):
        self.block_id = block_id

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'ACM', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        acm = jsonpickle.decode(msg['obj_str'])
        return acm


class Block:
    """A block containing transactions.

    Args:
        creator_id (int): id of the node that created the block.
        parent_block_id (int): id of parent block.
        txs (list): list of Transaction instances.
        counter (int): used to define unqiue sequence number.

    Attributes:
        block_id (int): used to uniquely identify a block.
        SEQ (int): sequence number used to create unique block id.
        creator_state (int): 0,1 or 2 translates to QUICK, MEDIUM or SLOW.
        depth (int): Total number of transactions the block and all ist ancestor blocks contain.
    """
    def __init__(self, creator_id, parent_block_id, txs, counter):
        self.creator_id = creator_id
        self.SEQ = counter
        self.block_id = self.creator_id | (self.SEQ << 16)
        self.creator_state = None
        self.parent_block_id = parent_block_id
        self.txs = txs
        self.depth = None

    def __lt__(self, other):
        """Compare two blocks by depth` and `creator_id`."""
        if self.depth < other.depth:
            return True

        if self.depth > other.depth:
            return False

        return self.creator_id < other.creator_id

    def __eq__(self, other):
        return self.block_id == other.block_id

    def __hash__(self):
        return 0

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'BLK', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        blk = jsonpickle.decode(msg['obj_str'])
        return blk


class Transaction:
    """ A Transaction contains a content field wich can store an arbitrary string. This can for example be a database-
    operation.

    Args:
        creator_id (int): id of the node that created the transaction.
        content (str): the command to be stored/executed/committed.
        counter (int): used to define unqiue sequence number.

    Attributes:
        SEQ (int): used to define unique transaction id.
        txn_id (int): used to uniquely identify a transaction.
    """
    def __init__(self, creator_id, content, counter):
        self.creator_id = creator_id
        self.SEQ = counter
        self.txn_id = self.creator_id | (self.SEQ << 16)
        self.content = content  # a string which can represent a command for example

    def __eq__(self, other):
        return self.txn_id == other.txn_id

    def __hash__(self):
        return 0

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'TXN', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        txn = jsonpickle.decode(msg['obj_str'])
        return txn


class PingMessage:
    """"Is sent to estimate RTT.

    Args:
        time (float): timestamp marking the start.
    """
    def __init__(self, time):
        self.time = time

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'PIN', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        ping = jsonpickle.decode(msg['obj_str'])
        return ping


class PongMessage:
    """"Is sent to estimate RTT.

    Args:
        time (float): timestamp that was received in the PingMessage.
    """
    def __init__(self, time):
        self.time = time  

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'PON', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        pong = jsonpickle.decode(msg['obj_str'])
        return pong
