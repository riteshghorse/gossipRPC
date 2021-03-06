"""
Author: Shreyas M

A common method for sending sync messages.
"""
class SynGossipDigest(object):

    def __init__(self, clusterId, gDigestList):
        self._clusterId = clusterId
        self._gDigestList = gDigestList

    @staticmethod
    def getGossipDigest(receivedMsg):
        return receivedMsg['_gDigestList']