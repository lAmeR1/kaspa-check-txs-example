import asyncio
import logging
import time

from kaspad.KaspadMultiClient import KaspadMultiClient

# get file logger
logging.basicConfig(format="%(asctime)s::%(levelname)s::%(name)s::%(message)s", level=logging.ERROR,
                    handlers=[logging.StreamHandler()])
_logger = logging.getLogger(__name__)
kaspad_hosts = ["seeder2.kaspad.net:16110"]


async def main():
    # create Kaspad client
    client = KaspadMultiClient(kaspad_hosts)
    await client.initialize_all()

    # for this example, just start at the tip of the blockdag.. need to wait a few seconds
    daginfo = await client.request("getBlockDagInfoRequest", {})
    start_hash = daginfo["getBlockDagInfoResponse"]["tipHashes"][0]

    _logger.info(f"Start hash: {start_hash}")

    # wait a few seconds, so we have some data..
    time.sleep(8)

    blocks = await client.request("getBlocksRequest",
                                  {"lowHash": start_hash,
                                   "includeBlocks": True,
                                   "includeTransactions": True})

    for block in blocks["getBlocksResponse"]["blocks"]:
        print(f'New block found: {block["verboseData"]["hash"]}')
        print(f'TXs in block: {[x["verboseData"]["transactionId"] for x in block["transactions"]]}')

    vspc = await client.request("getVirtualSelectedParentChainFromBlockRequest",
                                {"startHash": start_hash,
                                 "includeAcceptedTransactionIds": True})

    # first set is-accepted to false for removed blocks
    for removed_block_id in vspc.get("removedChainBlockHashes") or []:
        print(f"Removed block {removed_block_id}. All TXs inside are now NOT ACCEPTED!")
        # set the TXs in your database / cache to not accepted

    for tx_accept_dict in vspc["getVirtualSelectedParentChainFromBlockResponse"]["acceptedTransactionIds"]:
        print(
            f"VirtualSelectParentChainBlock (isChainBlock=True) {tx_accept_dict['acceptingBlockHash']} just accepted the following TXs: {tx_accept_dict['acceptedTransactionIds']}")
        last_known_vscp_block = tx_accept_dict['acceptingBlockHash']
        # note: you only can set TXs as valid, if you know the TX already. So you need to execute
        # getBlocks BEFORE getVirtualSelectedParentChainFromBlockRequest

    """
    start again with:
    read next blocks with
    lowHash = blocks["getBlocksResponse"]["blocks"][-1]["verboseData"]["hash"]
    and vspc getVirtualSelectedParentChainFromBlockRequest: startHash = last_known_vscp_block
    """


if __name__ == '__main__':
    asyncio.run(main())
