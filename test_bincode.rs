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

fn main() {
    let params = PlaceOrderParams {
        side: OrderSide::Sell,
        amount: 5000000,
        order_type: OrderParamsType::Limit {
            tif: TimeInForce::GTC,
        },
        limit_price: 50000000000,
    };
    
    let serialized = bincode::serialize(&params).unwrap();
    println!("Rust bincode序列化长度: {} 字节", serialized.len());
    println!("Rust bincode十六进制: {}", hex::encode(&serialized));
    
    // 分析每个字节
    println!("\n字节分析:");
    for (i, byte) in serialized.iter().enumerate() {
        println!("  [{:2}]: 0x{:02x} ({})", i, byte, byte);
    }
}