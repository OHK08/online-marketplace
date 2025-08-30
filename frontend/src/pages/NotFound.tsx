import { useLocation } from "react-router-dom";
import { useEffect } from "react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error(
      "404 Error: User attempted to access non-existent route:",
      location.pathname
    );
  }, [location.pathname]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-pink-100 via-purple-100 to-blue-100 p-6">
      <img
        src="https://cdnl.iconscout.com/lottie/premium/thumb/error-404-animation-gif-download-4699352.gif"
        alt="Lost meme"
        className="w-64 h-64 mb-6 rounded-2xl shadow-lg"
      />
      <p className="text-2xl text-gray-700 mb-2">Oops! This page took a wrong turn 🚗💨</p>
      <p className="text-lg text-gray-500 mb-6 italic">
        “I would tell you a joke about 404 errors… but you wouldn’t find it.” 😅
      </p>

      <a
        href="/"
        className="px-6 py-3 bg-purple-600 text-white text-lg font-semibold rounded-xl shadow-lg hover:bg-purple-700 transition duration-300"
      >
        Take Me Home
      </a>

      <p className="mt-6 text-sm text-gray-500">
        Lost? Don’t worry, even Google Maps messes up sometimes.
      </p>
    </div>
  );
};

export default NotFound;
