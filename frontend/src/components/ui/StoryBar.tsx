import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

const mockStories = [
  { id: '1', name: 'Sarah', avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b714?w=100' },
  { id: '2', name: 'Mike', avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100' },
  { id: '3', name: 'Emma', avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100' },
];

export const StoryBar = () => {
  return (
    <div className="flex gap-4 overflow-x-auto pb-2">
      {mockStories.map((story) => (
        <div key={story.id} className="flex flex-col items-center gap-2 cursor-pointer">
          <div className="story-ring p-0.5 rounded-full">
            <Avatar className="w-16 h-16">
              <AvatarImage src={story.avatar} alt={story.name} />
              <AvatarFallback>{story.name[0]}</AvatarFallback>
            </Avatar>
          </div>
          <span className="text-xs text-muted-foreground">{story.name}</span>
        </div>
      ))}
    </div>
  );
};