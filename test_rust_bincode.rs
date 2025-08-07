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
    
    // 分析结构
    println!("\n结构分析:");
    println!("  side (OrderSide::Sell): {} -> 0x{:02x}", params.side as u32, params.side as u32);
    println!("  amount (u64): {} -> 0x{:016x}", params.amount, params.amount);
    println!("  order_type (OrderParamsType::Limit):");
    println!("    - variant index: 0");
    println!("    - tif (TimeInForce::GTC): {} -> 0x{:02x}", TimeInForce::GTC as u32, TimeInForce::GTC as u32);
    println!("  limit_price (u64): {} -> 0x{:016x}", params.limit_price, params.limit_price);
    
    // 测试单独序列化OrderParamsType
    let order_type = OrderParamsType::Limit { tif: TimeInForce::GTC };
    let order_type_serialized = bincode::serialize(&order_type).unwrap();
    println!("\nOrderParamsType::Limit {{ tif: TimeInForce::GTC }} 序列化:");
    println!("  十六进制: {}", hex::encode(&order_type_serialized));
    println!("  字节: {:?}", order_type_serialized);
}
