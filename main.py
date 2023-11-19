from web3 import AsyncWeb3
import httpx
import asyncio
import re


async def mint(to, rpc, private_key, gasPrice, maxFeePerGas, maxPriorityFeePerGas, data):
    web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc))
    account = web3.eth.account.from_key(private_key)
    http = httpx.AsyncClient()
    chain_id = await web3.eth.chain_id
    to = web3.to_checksum_address(to)
    nonce = await web3.eth.get_transaction_count(account.address)
    gasPrice = web3.to_wei(float(gasPrice), 'gwei')
    maxFeePerGas = web3.to_wei(float(maxFeePerGas), 'gwei')
    maxPriorityFeePerGas = web3.to_wei(float(maxPriorityFeePerGas), 'gwei')

    tx = {
        'from': account.address,
        'to': to,
        'nonce': nonce,
        'gas': 25024,
        'gasPrice': gasPrice,
        'maxFeePerGas': maxFeePerGas,
        'maxPriorityFeePerGas': maxPriorityFeePerGas,
        'chainId': chain_id,
        'data': data
    }

    if gasPrice == 0:
        del tx['gasPrice']
    else:
        del tx['maxFeePerGas']
        del tx['maxPriorityFeePerGas']

    res = re.findall(r'\[(\d+)-(\d+)\]', data)
    start, end, subtext = 0, 0, None
    if len(res) > 0:
        start = int(res[0][0])
        end = int(res[0][1])
        subtext = res[0][0] + '-' + res[0][1]

    time = 100
    if end - start > 10000:
        time = (end - start) // 100 + 1

    for x in range(0, time):
        request_list = []
        for i in range(0, 100):
            tx['nonce'] = nonce
            if subtext is None:
                if data.startswith('0x'):
                    tx['data'] = data
                else:
                    tx['data'] = web3.to_hex(text=data)
            else:
                tx['data'] = data.replace(subtext, str(start))
                start += 1
                if start > end:
                    print('已经到达最大范围')
                    return
            signed = account.sign_transaction(tx)
            nonce += 1
            request_list.append({"jsonrpc": "2.0", "method": "eth_sendRawTransaction", "params": [signed.rawTransaction.hex()], "id": i + 1})
        res = await http.post(rpc, json=request_list)
        print(res.json())
        await asyncio.sleep(1)


if __name__ == '__main__':
    print('hdd.cm, 推特低至2毛')
    _to = input('输入地址(打到那个号)：').strip()
    _private_key = input('输入私钥(有gas的小号)：').strip()
    _rpc = input('输入RPC：').strip()

    _eip1559 = input('输入是否EIP1559(1为是，0为否)：').strip()
    if _eip1559 == '1':
        _gasPrice = 0
        _maxFeePerGas = float(input('输入maxFeePerGas：').strip())
        _maxPriorityFeePerGas = float(input('输入maxPriorityFeePerGas：').strip())
    else:
        _gasPrice = float(input('输入gasPrice：').strip())
        _maxFeePerGas = 0
        _maxPriorityFeePerGas = 0

    print('可以直接输入【data:,{"p":"asc-20","op":"mint","tick":"aval","amt":"10"}】格式')
    print('也可以直接输入 0x646174613a2c7b 十六进制格式, 必须要有0x开头')
    print('动态范围, 请用方括号加范围，如[3242-8765]代替： {"p":"asc-20","op":"mint","id":"[3242-8765]","tick":"aval","amt":"10"}')
    print('注意只替换变动数字，不要替换其他的，如果有引号不要漏掉引号')

    _data = input('输入data：').strip()

    asyncio.run(mint(_to, _rpc, _private_key, _gasPrice, _maxFeePerGas, _maxPriorityFeePerGas, _data))
