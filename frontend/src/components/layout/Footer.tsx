// src/components/layout/Footer.tsx
const Footer = () => {
  return (
    <footer className="border-t py-8">
      <div className="max-w-7xl mx-auto px-4 text-center text-muted-foreground">
        <p>&copy; {new Date().getFullYear()} MarketPlace. Discover. Connect. Grow. Together in our marketplace.</p>
      </div>
    </footer>
  );
};

export default Footer;
