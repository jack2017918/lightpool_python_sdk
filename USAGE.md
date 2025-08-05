# LightPool Python SDK 使用说明

## 安装

确保您已安装Python 3.8+和pip。

```bash
# 克隆项目
git clone <repository-url>
cd lightpool_python_sdk

# 安装依赖
pip install -r requirements.txt

# 安装SDK到开发环境（推荐）
pip install -e .
```

## 快速开始

### 1. 安装依赖

```bash
cd lightpool_python_sdk
pip install -r requirements.txt
```

### 2. 确保LightPool节点运行

确保您的LightPool节点正在运行，并且RPC服务在端口26300上可用：

```bash
# 在另一个终端中运行
cargo run --release --bin lightpool -- -vv run --keys data/node1/node.json --committee data/node1/committee.json --store data/node1/store
```

### 3. 运行示例

#### 简单现货交易示例

```bash
python examples/simple_spot_client.py
```

这个示例会：
- 创建BTC和USDT代币
- 创建BTC/USDT交易市场
- 下卖单和买单
- 演示订单匹配和撤单

#### 高频交易示例

```bash
python examples/burst_spot_client.py
```

这个示例会：
- 批量创建多个代币和市场
- 进行高频下单测试
- 提供性能统计

## 命令行工具使用

### 基本命令

```bash
# 健康检查
python -m lightpool_sdk.cli health

# 创建代币
python -m lightpool_sdk.cli create-token \
  --name "Bitcoin" \
  --symbol "BTC" \
  --decimals 6 \
  --total-supply 21000000000000 \
  --mintable

# 创建市场
python -m lightpool_sdk.cli create-market \
  --name "BTC/USDT" \
  --base-token "0x..." \
  --quote-token "0x..." \
  --min-order-size 100000 \
  --tick-size 1000000

# 下单
python -m lightpool_sdk.cli place-order \
  --market-address "0x..." \
  --market-id "0x..." \
  --balance-id "0x..." \
  --side buy \
  --amount 1000000 \
  --price 50000000000

# 撤单
python -m lightpool_sdk.cli cancel-order \
  --market-address "0x..." \
  --market-id "0x..." \
  --order-id "0x..."

# 查询订单簿
python -m lightpool_sdk.cli order-book \
  --market-id "0x..." \
  --depth 10

# 查询交易历史
python -m lightpool_sdk.cli trades \
  --market-id "0x..." \
  --limit 100

# 查询用户订单
python -m lightpool_sdk.cli orders \
  --address "0x..."
```

### 使用私钥

```bash
# 使用指定私钥
python -m lightpool_sdk.cli --private-key "0x1234..." create-token --name "Test" --symbol "TEST" --total-supply 1000000
```

## 编程接口使用

### 基本设置

```python
import asyncio
from lightpool_sdk import (
    LightPoolClient, Signer, TransactionBuilder, ActionBuilder,
    Address, ObjectID, U256,
    CreateTokenParams, CreateMarketParams, PlaceOrderParams,
    OrderSide, TimeInForce, MarketState, LimitOrderParams,
    TOKEN_CONTRACT_ADDRESS, SPOT_CONTRACT_ADDRESS
)

async def main():
    # 创建客户端
    client = LightPoolClient("http://localhost:26300")
    
    # 创建签名者
    signer = Signer.new()  # 或使用 Signer.from_hex("0x...")
    
    # 测试连接
    is_healthy = await client.health_check()
    print(f"节点健康状态: {is_healthy}")
```

### 创建代币

```python
async def create_token_example(client, signer):
    # 创建代币参数
    create_params = CreateTokenParams(
        name="Bitcoin",
        symbol="BTC",
        decimals=6,
        total_supply=U256(21_000_000_000_000),  # 21M BTC
        mintable=True,
        to=signer.address()
    )
    
    # 构建操作
    action = ActionBuilder.create_token(TOKEN_CONTRACT_ADDRESS, create_params)
    
    # 构建并签名交易
    tx = TransactionBuilder.new()\
        .sender(signer.address())\
        .expiration(0xFFFFFFFFFFFFFFFF)\
        .add_action(action)\
        .build_and_sign(signer)
    
    # 提交交易
    response = await client.submit_transaction(tx)
    
    if response["receipt"].is_success():
        print(f"✅ 代币创建成功: {response['digest']}")
        return response["digest"]
    else:
        print("❌ 代币创建失败")
        return None
```

### 创建市场

```python
async def create_market_example(client, signer, base_token, quote_token):
    # 创建市场参数
    market_params = CreateMarketParams(
        name="BTC/USDT",
        base_token=base_token,
        quote_token=quote_token,
        min_order_size=100_000,  # 0.1 BTC
        tick_size=1_000_000,     # 1 USDT
        maker_fee_bps=10,        # 0.1%
        taker_fee_bps=20,        # 0.2%
        allow_market_orders=True,
        state=MarketState.ACTIVE,
        limit_order=True
    )
    
    # 构建操作
    action = ActionBuilder.create_market(SPOT_CONTRACT_ADDRESS, market_params)
    
    # 构建并签名交易
    tx = TransactionBuilder.new()\
        .sender(signer.address())\
        .expiration(0xFFFFFFFFFFFFFFFF)\
        .add_action(action)\
        .build_and_sign(signer)
    
    # 提交交易
    response = await client.submit_transaction(tx)
    
    if response["receipt"].is_success():
        print(f"✅ 市场创建成功: {response['digest']}")
        return response["digest"]
    else:
        print("❌ 市场创建失败")
        return None
```

### 下单

```python
async def place_order_example(client, signer, market_address, market_id, balance_id):
    # 创建订单参数
    order_params = PlaceOrderParams(
        side=OrderSide.BUY,
        amount=1_000_000,  # 1 BTC
        order_type=LimitOrderParams(TimeInForce.GTC),
        limit_price=50_000_000_000  # 50,000 USDT
    )
    
    # 构建操作
    action = ActionBuilder.place_order(
        market_address,
        market_id,
        balance_id,
        order_params
    )
    
    # 构建并签名交易
    tx = TransactionBuilder.new()\
        .sender(signer.address())\
        .expiration(0xFFFFFFFFFFFFFFFF)\
        .add_action(action)\
        .build_and_sign(signer)
    
    # 提交交易
    response = await client.submit_transaction(tx)
    
    if response["receipt"].is_success():
        print(f"✅ 下单成功: {response['digest']}")
        return response["digest"]
    else:
        print("❌ 下单失败")
        return None
```

### 撤单

```python
async def cancel_order_example(client, signer, market_address, market_id, order_id):
    from lightpool_sdk import CancelOrderParams
    
    # 创建撤单参数
    cancel_params = CancelOrderParams(order_id=order_id)
    
    # 构建操作
    action = ActionBuilder.cancel_order(
        market_address,
        market_id,
        cancel_params
    )
    
    # 构建并签名交易
    tx = TransactionBuilder.new()\
        .sender(signer.address())\
        .expiration(0xFFFFFFFFFFFFFFFF)\
        .add_action(action)\
        .build_and_sign(signer)
    
    # 提交交易
    response = await client.submit_transaction(tx)
    
    if response["receipt"].is_success():
        print(f"✅ 撤单成功: {response['digest']}")
        return response["digest"]
    else:
        print("❌ 撤单失败")
        return None
```

### 查询功能

```python
async def query_examples(client):
    # 查询订单簿
    order_book = await client.get_order_book(market_id, depth=10)
    if order_book:
        print("订单簿:", order_book)
    
    # 查询交易历史
    trades = await client.get_trades(market_id, limit=100)
    if trades:
        print("交易历史:", trades)
    
    # 查询用户订单
    orders = await client.get_orders(address)
    if orders:
        print("用户订单:", orders)
    
    # 查询市场信息
    market_info = await client.get_market_info(market_id)
    if market_info:
        print("市场信息:", market_info)
```

## 错误处理

```python
from lightpool_sdk import (
    NetworkError, CryptoError, TransactionError,
    ValidationError, RpcError
)

async def error_handling_example():
    try:
        # 执行操作
        response = await client.submit_transaction(tx)
        print("操作成功")
        
    except NetworkError as e:
        print(f"网络错误: {e}")
    except CryptoError as e:
        print(f"加密错误: {e}")
    except TransactionError as e:
        print(f"交易错误: {e}")
    except ValidationError as e:
        print(f"验证错误: {e}")
    except RpcError as e:
        print(f"RPC错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")
```

## 高级功能

### 批量操作

```python
async def batch_operations_example(client, signer):
    # 创建多个操作
    actions = []
    
    # 添加代币创建操作
    for i in range(5):
        create_params = CreateTokenParams(
            name=f"Token{i}",
            symbol=f"TKN{i}",
            decimals=6,
            total_supply=U256(1_000_000_000_000),
            mintable=True,
            to=signer.address()
        )
        action = ActionBuilder.create_token(TOKEN_CONTRACT_ADDRESS, create_params)
        actions.append(action)
    
    # 构建包含多个操作的交易
    tx_builder = TransactionBuilder.new()\
        .sender(signer.address())\
        .expiration(0xFFFFFFFFFFFFFFFF)
    
    for action in actions:
        tx_builder = tx_builder.add_action(action)
    
    tx = tx_builder.build_and_sign(signer)
    
    # 提交批量交易
    response = await client.submit_transaction(tx)
    print(f"批量操作结果: {response}")
```

### 异步并发

```python
async def concurrent_trading_example(client, signer, markets):
    # 并发下单
    tasks = []
    for market in markets:
        task = place_order_async(client, signer, market)
        tasks.append(task)
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"任务 {i} 失败: {result}")
        else:
            print(f"任务 {i} 成功: {result}")
```

## 性能优化建议

1. **连接复用**: 使用异步上下文管理器复用HTTP连接
2. **批量操作**: 将多个操作合并到单个交易中
3. **并发处理**: 使用asyncio进行并发操作
4. **错误重试**: 实现指数退避重试机制
5. **连接池**: 对于高频交易，考虑使用连接池

## 常见问题

### Q: 如何处理网络连接问题？

A: 实现重试机制和错误处理：

```python
import asyncio
from lightpool_sdk import NetworkError

async def submit_with_retry(client, tx, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.submit_transaction(tx)
        except NetworkError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # 指数退避
```

### Q: 如何获取真实的代币ID和余额ID？

A: 从交易事件中解析：

```python
def extract_token_info(receipt):
    for event in receipt.events:
        if event.event_type == "token_created":
            # 解析事件数据获取代币信息
            return event.data
    return None
```

### Q: 如何监控订单状态？

A: 定期查询订单状态：

```python
async def monitor_order(client, order_id, market_id):
    while True:
        orders = await client.get_orders(signer.address(), market_id)
        for order in orders:
            if order["id"] == order_id:
                print(f"订单状态: {order['status']}")
                if order["status"] in ["filled", "cancelled"]:
                    return order
        await asyncio.sleep(1)
```

## 更多示例

查看 `examples/` 目录中的完整示例代码：

- `simple_spot_client.py`: 基础现货交易示例
- `burst_spot_client.py`: 高频交易性能测试示例

这些示例提供了完整的工作流程，可以作为您开发的参考。 