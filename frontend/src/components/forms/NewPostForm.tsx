import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Sparkles } from 'lucide-react';
import { useState } from 'react';
import { aiClient } from '@/services/aiClient';

const newPostSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  price: z.number().min(0.01, 'Price must be greater than 0'),
  category: z.string().min(1, 'Category is required'),
  stock: z.number().min(0, 'Stock cannot be negative'),
  status: z.enum(['Draft', 'Published']),
});

type NewPostFormData = z.infer<typeof newPostSchema>;

export const NewPostForm = () => {
  const [isGenerating, setIsGenerating] = useState(false);

  const form = useForm<NewPostFormData>({
    resolver: zodResolver(newPostSchema),
    defaultValues: {
      title: '', description: '', price: 0, category: '', stock: 0, status: 'Draft'
    },
  });

  const generateCaption = async () => {
    setIsGenerating(true);
    try {
      const title = form.getValues('title');
      const { text } = await aiClient.generate({
        type: 'caption',
        prompt: `Product: ${title}`,
      });
      form.setValue('description', text);
    } catch (error) {
      console.error('Failed to generate caption:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const onSubmit = (data: NewPostFormData) => {
    console.log('New post data:', data);
    // Handle form submission
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Product Title</FormLabel>
              <FormControl>
                <Input placeholder="Enter product title" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <div className="flex items-center justify-between">
                <FormLabel>Description</FormLabel>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={generateCaption}
                  disabled={isGenerating || !form.getValues('title')}
                  className="flex items-center gap-2"
                >
                  <Sparkles className="w-4 h-4" />
                  {isGenerating ? 'Generating...' : 'AI Suggest'}
                </Button>
              </div>
              <FormControl>
                <Textarea placeholder="Describe your product" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="price"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Price ($)</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    {...field}
                    onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          
          <FormField
            control={form.control}
            name="stock"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Stock</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    placeholder="0"
                    {...field}
                    onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="category"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Category</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="art">Art & Crafts</SelectItem>
                    <SelectItem value="fashion">Fashion</SelectItem>
                    <SelectItem value="home">Home & Garden</SelectItem>
                    <SelectItem value="jewelry">Jewelry</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="status"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Status</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="Draft">Draft</SelectItem>
                    <SelectItem value="Published">Published</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <Button type="submit" className="w-full btn-gradient">
          Save Product
        </Button>
      </form>
    </Form>
  );
};