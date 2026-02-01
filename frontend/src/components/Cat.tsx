'use client';

import React, { useState, useEffect, useCallback } from 'react';
import styles from './Cat.module.css';

type CatAction = 'idle' | 'sleep' | 'stretch' | 'jump' | 'walk-left' | 'walk-right' | 'meow' | 'happy';

interface CatState {
    action: CatAction;
    x: number;
    y: number;
    facing: 'left' | 'right';
}

interface CatProps {
    showOnAllPages?: boolean;
    initialGreeting?: boolean;
}

export default function Cat({ showOnAllPages = true, initialGreeting = true }: CatProps) {
    const [catState, setCatState] = useState<CatState>({
        action: 'idle',
        x: 100,
        y: 150,
        facing: 'right',
    });

    const [greeting, setGreeting] = useState<string>('');
    const [showGreeting, setShowGreeting] = useState(false);
    const [isMobile, setIsMobile] = useState(false);
    const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

    const greetings = [
        '喵~',
        '你好呀~',
        '快来陪我玩!',
        '我想陪你走过这28天~',
        '一起加油吧!',
        '坚持就是胜利呢~',
        '相信自己，你可以的！',
        '今天心情怎么样呀？',
        '记得多喝水哦~',
        '你真棒！👍',
    ];

    // 检测窗口大小并初始化位置
    useEffect(() => {
        const updateWindowSize = () => {
            const width = window.innerWidth;
            const height = window.innerHeight;
            setWindowSize({ width, height });
            setIsMobile(width < 768);

            // 如果还没初始化过位置，或者窗口大小改变，确保猫在底部
            setCatState(prev => ({
                ...prev,
                y: height - 160 // 距离底部 160px
            }));
        };

        updateWindowSize();
        window.addEventListener('resize', updateWindowSize);
        return () => window.removeEventListener('resize', updateWindowSize);
    }, []);

    // 主动问候
    useEffect(() => {
        if (!initialGreeting || windowSize.width === 0) return;

        const greetingTimeout = setTimeout(() => {
            const randomGreeting = greetings[Math.floor(Math.random() * greetings.length)];
            setGreeting(randomGreeting);
            setShowGreeting(true);
            setTimeout(() => setShowGreeting(false), 3000);
        }, 2000);

        return () => clearTimeout(greetingTimeout);
    }, [initialGreeting, windowSize.width]);

    // 间歇性说话
    useEffect(() => {
        if (windowSize.width === 0) return;

        const talkInterval = setInterval(() => {
            const shouldTalk = Math.random() > 0.7; // 30% 概率说话
            if (shouldTalk && !showGreeting) {
                const randomGreeting = greetings[Math.floor(Math.random() * greetings.length)];
                setGreeting(randomGreeting);
                setShowGreeting(true);
                setTimeout(() => setShowGreeting(false), 3000);
            }
        }, 15000 + Math.random() * 10000); // 15-25秒随机间隔

        return () => clearInterval(talkInterval);
    }, [showGreeting, windowSize.width]);

    // 自动动作循环
    useEffect(() => {
        if (windowSize.width === 0) return;

        // 决策循环：决定做什么动作
        const decisionInterval = setInterval(() => {
            const actions: CatAction[] = ['idle', 'stretch', 'walk-left', 'walk-right', 'idle', 'sleep'];
            const randomAction = actions[Math.floor(Math.random() * actions.length)];

            setCatState((prev) => {
                // 如果当前正在睡觉，有一定概率继续睡
                if (prev.action === 'sleep' && Math.random() > 0.3) {
                    return prev;
                }

                let newFacing = prev.facing;
                if (randomAction === 'walk-left') newFacing = 'left';
                if (randomAction === 'walk-right') newFacing = 'right';

                return {
                    ...prev,
                    action: randomAction,
                    facing: newFacing,
                };
            });
        }, 4000); // 每4秒决定一次新动作

        // 移动循环：处理平滑移动
        const moveInterval = setInterval(() => {
            setCatState((prev) => {
                // 只有在走路状态下才移动
                if (prev.action !== 'walk-left' && prev.action !== 'walk-right') {
                    return prev;
                }

                let newX = prev.x;
                let newY = prev.y;
                const speed = 4; // 移动速度 (像素/帧)

                if (prev.action === 'walk-left') {
                    newX = Math.max(20, prev.x - speed);
                    // 走到边缘自动停下
                    if (newX <= 20) return { ...prev, action: 'idle' };
                } else if (prev.action === 'walk-right') {
                    newX = Math.min(windowSize.width - 140, prev.x + speed);
                    // 走到边缘自动停下
                    if (newX >= windowSize.width - 140) return { ...prev, action: 'idle' };
                }

                // Y轴移动：随机上下漂移，实现自由走动感
                // 限制在屏幕区域内：保留顶部 30% 空间给内容，底部保留 20px
                const minY = windowSize.height * 0.3;
                const maxY = windowSize.height - 160;

                // 30% 概率改变 Y
                if (Math.random() > 0.7) {
                    const yChange = (Math.random() - 0.5) * 6; // -3 到 +3
                    newY = Math.max(minY, Math.min(maxY, prev.y + yChange));
                }

                return {
                    ...prev,
                    x: newX,
                    y: newY,
                };
            });
        }, 50); // 每50ms更新一次位置 (20fps)

        return () => {
            clearInterval(decisionInterval);
            clearInterval(moveInterval);
        };
    }, [windowSize.width]);

    const handleCatClick = useCallback(() => {
        const actions: CatAction[] = ['jump', 'meow', 'happy', 'stretch'];
        const randomAction = actions[Math.floor(Math.random() * actions.length)];

        setCatState((prev) => ({
            ...prev,
            action: randomAction,
        }));

        setTimeout(() => {
            setCatState((prev) => ({
                ...prev,
                action: 'idle',
            }));
        }, 1000);

        const interactions = [
            '喵喵!',
            '你好!',
            '再摸我啦~',
            '我好开心!',
            '你真温柔呢~',
            '继续加油哦~',
            '我会陪着你!',
            '你太可爱了!',
            '嘿嘿嘿~',
            '要抱抱吗？',
            '我爱你！❤️',
        ];
        const randomInteraction = interactions[Math.floor(Math.random() * interactions.length)];
        setGreeting(randomInteraction);
        setShowGreeting(true);
        setTimeout(() => setShowGreeting(false), 2500);
    }, []);

    // 移动设备时隐藏小猫
    if (isMobile && !showOnAllPages) {
        return null;
    }

    // 等待窗口大小初始化
    if (windowSize.width === 0) {
        return null;
    }

    return (
        <div className={styles.catContainer}>
            {/* 问候气泡 */}
            {showGreeting && (
                <div
                    className={styles.greetingBubble}
                    style={{
                        left: `${Math.max(20, Math.min(catState.x + 30, windowSize.width - 150))}px`,
                        top: `${Math.max(20, catState.y - 50)}px`,
                    }}
                >
                    {greeting}
                </div>
            )}

            {/* 小猫 */}
            <div
                className={styles.cat}
                style={{
                    left: `${catState.x}px`,
                    top: `${catState.y}px`,
                    transform: catState.facing === 'left' ? 'scaleX(-1)' : 'scaleX(1)',
                }}
                onClick={handleCatClick}
                role="button"
                tabIndex={0}
                aria-label="可爱的丑猫，点击与它互动"
                onKeyPress={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        handleCatClick();
                    }
                }}
            >
                {/* 头 */}
                <div className={`${styles.head} ${styles[catState.action]}`}>
                    {/* 耳朵 */}
                    <div className={`${styles.ear} ${styles.earLeft}`}></div>
                    <div className={`${styles.ear} ${styles.earRight}`}></div>

                    {/* 脸 */}
                    <div className={styles.face}>
                        {/* 眼睛 */}
                        <div className={styles.eyesContainer}>
                            <div className={`${styles.eye} ${styles.eyeLeft} ${styles[catState.action]}`}>
                                <div className={styles.eyeball}>
                                    <div className={styles.pupil}></div>
                                </div>
                            </div>
                            <div className={`${styles.eye} ${styles.eyeRight} ${styles[catState.action]}`}>
                                <div className={styles.eyeball}>
                                    <div className={styles.pupil}></div>
                                </div>
                            </div>
                        </div>

                        {/* 鼻子 */}
                        <div className={styles.nose}></div>

                        {/* 嘴 */}
                        <div className={`${styles.mouth} ${styles[catState.action]}`}></div>

                        {/* 胡须 - 左侧 */}
                        <div className={`${styles.whiskers} ${styles.whiskersLeft}`}>
                            <div className={styles.whisker}></div>
                            <div className={styles.whisker}></div>
                            <div className={styles.whisker}></div>
                        </div>
                        {/* 胡须 - 右侧 */}
                        <div className={`${styles.whiskers} ${styles.whiskersRight}`}>
                            <div className={styles.whisker}></div>
                            <div className={styles.whisker}></div>
                            <div className={styles.whisker}></div>
                        </div>
                    </div>
                </div>

                {/* 身体 */}
                <div className={`${styles.body} ${styles[catState.action]}`}>
                    {/* 前腿 */}
                    <div className={`${styles.leg} ${styles.legFrontLeft} ${styles[catState.action]}`}></div>
                    <div className={`${styles.leg} ${styles.legFrontRight} ${styles[catState.action]}`}></div>

                    {/* 后腿 */}
                    <div className={`${styles.leg} ${styles.legBackLeft} ${styles[catState.action]}`}></div>
                    <div className={`${styles.leg} ${styles.legBackRight} ${styles[catState.action]}`}></div>

                    {/* 尾巴 */}
                    <div className={`${styles.tail} ${styles[catState.action]}`}></div>
                </div>
            </div>

            {/* 交互提示 */}
            {!isMobile && (
                <div className={styles.interactionHint}>点击丑猫与它互动 ✨</div>
            )}
        </div>
    );
}
