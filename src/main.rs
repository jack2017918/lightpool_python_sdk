// 测试PlaceOrderParams的bincode序列化
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OrderSide {
    Buy,
    Sell,
}

#[derive(Debug, Clone, PartialEq, Eq, Copy, Serialize, Deserialize)]
pub enum TimeInForce {
    GTC,
    IOC,
    FOK,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OrderParamsType {
    Limit {
        tif: TimeInForce,
    },
    Market {
        slippage: u64,
    },
    Trigger {
        trigger_price: u64,
        is_market: bool,
        trigger_type: u8, // simplified
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlaceOrderParams {
    pub side: OrderSide,
    pub amount: u64,
    pub order_type: OrderParamsType,
    pub limit_price: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Action {
    pub inputs: Vec<[u8; 32]>,  // ObjectID as [u8; 32]
    pub contract: [u8; 32],     // Address as [u8; 32]
    pub action: u64,            // Name as u64
    pub params: Vec<u8>,
}

fn main() {
    // 测试PlaceOrderParams的bincode序列化
    let params = PlaceOrderParams {
        side: OrderSide::Sell,
        amount: 5000000,
        order_type: OrderParamsType::Limit {
            tif: TimeInForce::GTC,
        },
        limit_price: 50000000000,
    };
    
    let bincode_bytes = bincode::serialize(&params).unwrap();
    println!("PlaceOrderParams bincode: {}", hex::encode(&bincode_bytes));
    println!("PlaceOrderParams bincode length: {} bytes", bincode_bytes.len());
    
    // 测试Action的JSON序列化
    let action = Action {
        inputs: vec![
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 31, 2, 32, 198, 126, 27, 175, 248, 230, 183, 248, 87, 124, 96, 142, 205, 87],
            [150, 156, 61, 36, 204, 43, 19, 131, 100, 227, 132, 75, 150, 44, 159, 138, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 28]
        ],
        contract: [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        action: 746789037603618816,
        params: vec![1, 0, 0, 0, 64, 75, 76, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 116, 59, 164, 11, 0, 0, 0],
    };
    
    let json_str = serde_json::to_string(&action).unwrap();
    println!("Action JSON: {}", json_str);
    println!("Action JSON length: {} chars", json_str.len());
} 