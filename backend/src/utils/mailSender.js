const nodemailer = require("nodemailer");

const mailSender = async (email, title, body) => {
  try {
    let transporter = nodemailer.createTransport({
      host: process.env.MAIL_HOST || "smtp.gmail.com",
      port: 465,
      secure: true, // true for 465, false for 587
      auth: {
        user: process.env.MAIL_USER,
        pass: process.env.MAIL_PASSWORD,
      },
    });

    // Verify SMTP connection
    transporter.verify((err, success) => {
      if (err) {
        console.error("SMTP connection error:", err);
      } else {
        console.log("SMTP ready");
      }
    });

    let info = await transporter.sendMail({
      from: `"ORCHID MarketPlace" <${process.env.MAIL_USER}>`, // must match auth user
      to: email,
      subject: title,
      html: body,
    });

    console.log("Email sent:", info.messageId);
    return info;
  } catch (error) {
    console.error("Email send error:", error);
    throw error;
  }
};

module.exports = mailSender;
