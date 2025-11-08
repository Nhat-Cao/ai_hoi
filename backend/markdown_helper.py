def parse_restaurant_markdown(markdown_content: str):
    """Parse markdown content and extract restaurant information."""
    restaurants = []
    current_restaurant = {}
    
    lines = markdown_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line or (line.startswith('#') and not line.startswith('##')) or line.startswith('---') or line.startswith('*'):
            if current_restaurant:
                restaurants.append(current_restaurant)
                current_restaurant = {}
            continue
            
        if line.startswith('##'):
            if current_restaurant:
                restaurants.append(current_restaurant)
            # Simply remove '##' and any leading/trailing whitespace
            restaurant_name = line.replace('##', '').strip()
            print(restaurant_name)
            current_restaurant = {'name': restaurant_name}
            continue
        print(current_restaurant)  
        if line.startswith('- **'):
            key = line.split('**')[1].lower().strip(':')
            value = line.split('**: ')[1].strip()
            if key == 'địa chỉ':
                current_restaurant['address'] = value
            elif key == 'món đặc sắc':
                current_restaurant['specialty'] = value
            elif key == 'giá':
                current_restaurant['price'] = value
            elif key == 'mô tả':
                current_restaurant['description'] = value
                
    # Add the last restaurant if exists
    if current_restaurant:
        restaurants.append(current_restaurant)
        
    return restaurants

def restaurant_to_text(restaurant: dict) -> str:
    """Convert restaurant information to searchable text format."""
    return f"""Nhà hàng: {restaurant.get('name', '')}
Địa chỉ: {restaurant.get('address', '')}
Món đặc sắc: {restaurant.get('specialty', '')}
Giá: {restaurant.get('price', '')}
Mô tả: {restaurant.get('description', '')}"""