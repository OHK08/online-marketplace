import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { NewPostForm } from '@/components/forms/NewPostForm';
import { InventoryTable } from '@/components/seller/InventoryTable';
import { OrdersTable } from '@/components/seller/OrdersTable';
import { Plus, Package, ShoppingCart, BarChart } from 'lucide-react';

const SellerPage = () => {
  const [activeTab, setActiveTab] = useState('new-post');

  // Mock stats data
  const stats = [
    {
      title: 'Total Products',
      value: '24',
      icon: Package,
      description: '+2 from last month',
    },
    {
      title: 'Total Orders',
      value: '156',
      icon: ShoppingCart,
      description: '+12 from last week',
    },
    {
      title: 'Revenue',
      value: '$3,240',
      icon: BarChart,
      description: '+8% from last month',
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Seller Dashboard</h1>
          <p className="text-muted-foreground">
            Manage your products, orders, and grow your business
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {stats.map((stat, index) => (
            <Card key={index} className="card-hover">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">{stat.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="new-post" className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              New Post
            </TabsTrigger>
            <TabsTrigger value="stories">Stories</TabsTrigger>
            <TabsTrigger value="orders">Orders</TabsTrigger>
            <TabsTrigger value="inventory">Inventory</TabsTrigger>
          </TabsList>

          <TabsContent value="new-post" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Create New Product</CardTitle>
              </CardHeader>
              <CardContent>
                <NewPostForm />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="stories" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Stories</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12">
                  <h3 className="text-lg font-semibold mb-2">Stories Coming Soon</h3>
                  <p className="text-muted-foreground">
                    Share behind-the-scenes content and connect with your audience
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="orders" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Order Management</CardTitle>
              </CardHeader>
              <CardContent>
                <OrdersTable />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="inventory" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Product Inventory</CardTitle>
              </CardHeader>
              <CardContent>
                <InventoryTable />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default SellerPage;