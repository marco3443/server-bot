// ===== بوت إدارة Discord Server =====
// تأكد من تثبيت: npm install discord.js

const { Client, GatewayIntentBits, EmbedBuilder, PermissionFlagsBits, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');

// إعدادات البوت
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMembers,
        GatewayIntentBits.GuildModeration
    ]
});

// إعدادات البوت
const PREFIX = '!'; // يمكنك تغيير البادئة
const ADMIN_ROLE = 'Admin'; // اسم رتبة المشرفين
const MOD_ROLE = 'Moderator'; // اسم رتبة المراقبين

// رسالة عند تشغيل البوت
client.once('ready', () => {
    console.log(`✅ البوت ${client.user.tag} جاهز للعمل!`);
    client.user.setActivity('إدارة السيرفر | !help', { type: 'PLAYING' });
});

// ترحيب بالأعضاء الجدد
client.on('guildMemberAdd', member => {
    const channel = member.guild.channels.cache.find(ch => ch.name === 'general' || ch.name === 'welcome');
    if (!channel) return;

    const welcomeEmbed = new EmbedBuilder()
        .setColor('#00ff00')
        .setTitle('🎉 مرحباً بالعضو الجديد!')
        .setDescription(`أهلاً وسهلاً بك ${member} في **${member.guild.name}**!\n\nنتمنى لك وقتاً ممتعاً معنا!`)
        .setThumbnail(member.user.displayAvatarURL())
        .setFooter({ text: `العضو رقم: ${member.guild.memberCount}` })
        .setTimestamp();

    channel.send({ embeds: [welcomeEmbed] });
});

// وداع الأعضاء المغادرين
client.on('guildMemberRemove', member => {
    const channel = member.guild.channels.cache.find(ch => ch.name === 'general' || ch.name === 'goodbye');
    if (!channel) return;

    const goodbyeEmbed = new EmbedBuilder()
        .setColor('#ff0000')
        .setTitle('👋 وداعاً!')
        .setDescription(`**${member.user.tag}** غادر السيرفر.\n\nنتمنى له التوفيق!`)
        .setThumbnail(member.user.displayAvatarURL())
        .setTimestamp();

    channel.send({ embeds: [goodbyeEmbed] });
});

// معالج الرسائل والأوامر
client.on('messageCreate', async message => {
    if (message.author.bot) return;
    if (!message.content.startsWith(PREFIX)) return;

    const args = message.content.slice(PREFIX.length).trim().split(/ +/);
    const command = args.shift().toLowerCase();

    // ===== أوامر المساعدة =====
    if (command === 'help') {
        const helpEmbed = new EmbedBuilder()
            .setColor('#0099ff')
            .setTitle('📋 قائمة أوامر البوت')
            .setDescription('إليك جميع الأوامر المتاحة:')
            .addFields(
                { name: '👥 أوامر إدارة الأعضاء', value: '`!kick` - طرد عضو\n`!ban` - حظر عضو\n`!unban` - إلغاء حظر\n`!timeout` - كتم مؤقت\n`!warn` - إنذار عضو' },
                { name: '🔧 أوامر إدارة السيرفر', value: '`!clear` - حذف رسائل\n`!lock` - قفل قناة\n`!unlock` - فتح قناة\n`!slowmode` - وضع بطيء' },
                { name: '📊 أوامر المعلومات', value: '`!serverinfo` - معلومات السيرفر\n`!userinfo` - معلومات العضو\n`!membercount` - عدد الأعضاء' },
                { name: '🎮 أوامر التسلية', value: '`!ping` - سرعة البوت\n`!avatar` - صورة العضو\n`!say` - كرر رسالة' }
            )
            .setFooter({ text: 'استخدم البادئة ! قبل كل أمر' })
            .setTimestamp();

        message.channel.send({ embeds: [helpEmbed] });
    }

    // ===== أمر Ping =====
    else if (command === 'ping') {
        const sent = await message.channel.send('🏓 جاري الفحص...');
        const latency = sent.createdTimestamp - message.createdTimestamp;
        sent.edit(`🏓 **Pong!**\n📡 زمن الاستجابة: ${latency}ms\n💖 API Latency: ${Math.round(client.ws.ping)}ms`);
    }

    // ===== أمر طرد عضو =====
    else if (command === 'kick') {
        if (!message.member.permissions.has(PermissionFlagsBits.KickMembers)) {
            return message.reply('❌ ليس لديك صلاحية لاستخدام هذا الأمر!');
        }

        const user = message.mentions.users.first();
        if (!user) return message.reply('❌ يرجى منشن العضو المراد طرده!');

        const member = message.guild.members.cache.get(user.id);
        if (!member) return message.reply('❌ لم يتم العثور على هذا العضو!');
        if (!member.kickable) return message.reply('❌ لا يمكنني طرد هذا العضو!');

        const reason = args.slice(1).join(' ') || 'لم يتم تحديد سبب';

        try {
            await member.kick(reason);
            const kickEmbed = new EmbedBuilder()
                .setColor('#ff9900')
                .setTitle('👢 تم طرد عضو')
                .addFields(
                    { name: 'العضو المطرود', value: `${user.tag}`, inline: true },
                    { name: 'بواسطة', value: `${message.author.tag}`, inline: true },
                    { name: 'السبب', value: reason, inline: false }
                )
                .setTimestamp();

            message.channel.send({ embeds: [kickEmbed] });
        } catch (error) {
            console.error(error);
            message.reply('❌ حدث خطأ أثناء طرد العضو!');
        }
    }

    // ===== أمر حظر عضو =====
    else if (command === 'ban') {
        if (!message.member.permissions.has(PermissionFlagsBits.BanMembers)) {
            return message.reply('❌ ليس لديك صلاحية لاستخدام هذا الأمر!');
        }

        const user = message.mentions.users.first();
        if (!user) return message.reply('❌ يرجى منشن العضو المراد حظره!');

        const member = message.guild.members.cache.get(user.id);
        if (member && !member.bannable) return message.reply('❌ لا يمكنني حظر هذا العضو!');

        const reason = args.slice(1).join(' ') || 'لم يتم تحديد سبب';

        try {
            await message.guild.members.ban(user, { reason });
            const banEmbed = new EmbedBuilder()
                .setColor('#ff0000')
                .setTitle('🔨 تم حظر عضو')
                .addFields(
                    { name: 'العضو المحظور', value: `${user.tag}`, inline: true },
                    { name: 'بواسطة', value: `${message.author.tag}`, inline: true },
                    { name: 'السبب', value: reason, inline: false }
                )
                .setTimestamp();

            message.channel.send({ embeds: [banEmbed] });
        } catch (error) {
            console.error(error);
            message.reply('❌ حدث خطأ أثناء حظر العضو!');
        }
    }

    // ===== أمر إلغاء الحظر =====
    else if (command === 'unban') {
        if (!message.member.permissions.has(PermissionFlagsBits.BanMembers)) {
            return message.reply('❌ ليس لديك صلاحية لاستخدام هذا الأمر!');
        }

        const userId = args[0];
        if (!userId) return message.reply('❌ يرجى كتابة ID العضو المراد إلغاء حظره!');

        try {
            const user = await client.users.fetch(userId);
            await message.guild.members.unban(user);
            
            const unbanEmbed = new EmbedBuilder()
                .setColor('#00ff00')
                .setTitle('✅ تم إلغاء حظر عضو')
                .addFields(
                    { name: 'العضو', value: `${user.tag}`, inline: true },
                    { name: 'بواسطة', value: `${message.author.tag}`, inline: true }
                )
                .setTimestamp();

            message.channel.send({ embeds: [unbanEmbed] });
        } catch (error) {
            console.error(error);
            message.reply('❌ لم يتم العثور على هذا العضو في قائمة المحظورين!');
        }
    }

    // ===== أمر كتم مؤقت =====
    else if (command === 'timeout') {
        if (!message.member.permissions.has(PermissionFlagsBits.ModerateMembers)) {
            return message.reply('❌ ليس لديك صلاحية لاستخدام هذا الأمر!');
        }

        const user = message.mentions.users.first();
        const time = args[1];
        if (!user || !time) return message.reply('❌ الاستخدام: `!timeout @user <time>m` (مثال: 10m)');

        const member = message.guild.members.cache.get(user.id);
        if (!member) return message.reply('❌ لم يتم العثور على هذا العضو!');

        const duration = parseInt(time) * 60 * 1000; // تحويل لميللي ثانية
        const reason = args.slice(2).join(' ') || 'لم يتم تحديد سبب';

        try {
            await member.timeout(duration, reason);
            const timeoutEmbed = new EmbedBuilder()
                .setColor('#ffff00')
                .setTitle('🔇 تم كتم عضو مؤقتاً')
                .addFields(
                    { name: 'العضو', value: `${user.tag}`, inline: true },
                    { name: 'المدة', value: `${time} دقيقة`, inline: true },
                    { name: 'السبب', value: reason, inline: false }
                )
                .setTimestamp();

            message.channel.send({ embeds: [timeoutEmbed] });
        } catch (error) {
            console.error(error);
            message.reply('❌ حدث خطأ أثناء كتم العضو!');
        }
    }

    // ===== أمر حذف الرسائل =====
    else if (command === 'clear') {
        if (!message.member.permissions.has(PermissionFlagsBits.ManageMessages)) {
            return message.reply('❌ ليس لديك صلاحية لاستخدام هذا الأمر!');
        }

        const amount = parseInt(args[0]);
        if (!amount || amount < 1 || amount > 100) {
            return message.reply('❌ يرجى كتابة رقم بين 1 و 100!');
        }

        try {
            await message.channel.bulkDelete(amount + 1);
            const clearEmbed = new EmbedBuilder()
                .setColor('#9932cc')
                .setTitle('🧹 تم حذف الرسائل')
                .setDescription(`تم حذف **${amount}** رسالة بواسطة ${message.author}`)
                .setTimestamp();

            const reply = await message.channel.send({ embeds: [clearEmbed] });
            setTimeout(() => reply.delete(), 5000);
        } catch (error) {
            console.error(error);
            message.reply('❌ حدث خطأ أثناء حذف الرسائل!');
        }
    }

    // ===== أمر قفل القناة =====
    else if (command === 'lock') {
        if (!message.member.permissions.has(PermissionFlagsBits.ManageChannels)) {
            return message.reply('❌ ليس لديك صلاحية لاستخدام هذا الأمر!');
        }

        try {
            await message.channel.permissionOverwrites.edit(message.guild.roles.everyone, {
                SendMessages: false
            });

            const lockEmbed = new EmbedBuilder()
                .setColor('#ff4500')
                .setTitle('🔒 تم قفل القناة')
                .setDescription(`تم قفل ${message.channel} بواسطة ${message.author}`)
                .setTimestamp();

            message.channel.send({ embeds: [lockEmbed] });
        } catch (error) {
            console.error(error);
            message.reply('❌ حدث خطأ أثناء قفل القناة!');
        }
    }

    // ===== أمر فتح القناة =====
    else if (command === 'unlock') {
        if (!message.member.permissions.has(PermissionFlagsBits.ManageChannels)) {
            return message.reply('❌ ليس لديك صلاحية لاستخدام هذا الأمر!');
        }

        try {
            await message.channel.permissionOverwrites.edit(message.guild.roles.everyone, {
                SendMessages: null
            });

            const unlockEmbed = new EmbedBuilder()
                .setColor('#00ff00')
                .setTitle('🔓 تم فتح القناة')
                .setDescription(`تم فتح ${message.channel} بواسطة ${message.author}`)
                .setTimestamp();

            message.channel.send({ embeds: [unlockEmbed] });
        } catch (error) {
            console.error(error);
            message.reply('❌ حدث خطأ أثناء فتح القناة!');
        }
    }

    // ===== أمر معلومات السيرفر =====
    else if (command === 'serverinfo') {
        const guild = message.guild;
        const serverEmbed = new EmbedBuilder()
            .setColor('#00ff7f')
            .setTitle(`📊 معلومات سيرفر ${guild.name}`)
            .setThumbnail(guild.iconURL())
            .addFields(
                { name: '👑 المالك', value: `<@${guild.ownerId}>`, inline: true },
                { name: '👥 الأعضاء', value: `${guild.memberCount}`, inline: true },
                { name: '📅 تاريخ الإنشاء', value: guild.createdAt.toDateString(), inline: true },
                { name: '🌍 المنطقة', value: 'Auto', inline: true },
                { name: '🔗 القنوات', value: `${guild.channels.cache.size}`, inline: true },
                { name: '😀 الرموز', value: `${guild.emojis.cache.size}`, inline: true }
            )
            .setTimestamp();

        message.channel.send({ embeds: [serverEmbed] });
    }

    // ===== أمر معلومات العضو =====
    else if (command === 'userinfo') {
        const user = message.mentions.users.first() || message.author;
        const member = message.guild.members.cache.get(user.id);

        const userEmbed = new EmbedBuilder()
            .setColor('#4169e1')
            .setTitle(`👤 معلومات ${user.tag}`)
            .setThumbnail(user.displayAvatarURL())
            .addFields(
                { name: '🆔 ID', value: user.id, inline: true },
                { name: '📅 انضم لـ Discord', value: user.createdAt.toDateString(), inline: true },
                { name: '📅 انضم للسيرفر', value: member.joinedAt.toDateString(), inline: true },
                { name: '🎭 الرتب', value: member.roles.cache.map(role => role.name).join(', '), inline: false }
            )
            .setTimestamp();

        message.channel.send({ embeds: [userEmbed] });
    }

    // ===== أمر Say =====
    else if (command === 'say') {
        if (!message.member.permissions.has(PermissionFlagsBits.ManageMessages)) {
            return message.reply('❌ ليس لديك صلاحية لاستخدام هذا الأمر!');
        }

        const text = args.join(' ');
        if (!text) return message.reply('❌ يرجى كتابة النص المراد إرساله!');

        await message.delete();
        message.channel.send(text);
    }
});

// تسجيل الدخول (ضع التوكن الخاص بك هنا)
client.login('MTQxMzc0MDUzNDgwMzIwMjEyOQ.G6CF2e.e_isrxMI7cn76NAx3KQB9SWNgkIWeyKnKqsWc4')