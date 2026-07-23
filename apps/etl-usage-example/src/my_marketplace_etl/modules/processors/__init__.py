from my_marketplace_etl.modules.processors.order_processor import OrderProcessor
from my_marketplace_etl.modules.processors.product_processor import ProductProcessor
from my_marketplace_etl.modules.processors.traffic_processor import TrafficProcessor

marketplace_processors = {
    "order": OrderProcessor,
    "product": ProductProcessor,
    "traffic": TrafficProcessor,
}

marketplace_dependencies = {
    "order": ["order_payment"],
}
