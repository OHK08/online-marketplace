import apiClient from '@/lib/axios';

export interface Order {
  _id: string;
  buyerId: {
    _id: string;
    name: string;
    email: string;
  };
  artworkId: {
    _id: string;
    title: string;
    price: number;
    currency: string;
  };
  quantity: number;
  totalAmount: number;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  createdAt: string;
  updatedAt: string;
}

export interface OrderResponse {
  success: boolean;
  message?: string;
  order?: Order;
  orders?: Order[];
  count?: number;
}

export const orderService = {
  // For sellers - get orders for their artworks
  async getSellerOrders(): Promise<OrderResponse> {
    const response = await apiClient.get('/orders/seller/my-orders');
    return response.data;
  },

  // For buyers - get their orders
  async getBuyerOrders(): Promise<OrderResponse> {
    const response = await apiClient.get('/orders/buyer/my-orders'); 
    return response.data;
  },

  async getOrderById(id: string): Promise<OrderResponse> {
    const response = await apiClient.get(`/orders/${id}`);
    return response.data;
  },

  async updateOrderStatus(id: string, status: string): Promise<OrderResponse> {
    const response = await apiClient.patch(`/orders/${id}/status`, { status });
    return response.data;
  },
};