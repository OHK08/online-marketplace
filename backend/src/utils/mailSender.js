const nodemailer = require("nodemailer");

const mailSender = async (email, title, body) => {
  try {
    const transporter = nodemailer.createTransport({
      service: "SendGrid",
      auth: {
        user: "apikey", // this is fixed string for SendGrid
        pass: process.env.SENDGRID_API_KEY,
      },
    });

    let info = await transporter.sendMail({
      from: `Online MarketPlace <${process.env.MAIL_USER}>`,
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