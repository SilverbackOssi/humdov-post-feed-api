// JavaScript for dynamic interactions in the Humdov Post Feed API frontend

class PostFeedApp {
    constructor() {
        // Load current user ID from localStorage or use default (1)
        this.currentUserId = parseInt(localStorage.getItem('currentUserId') || '1');
        this.init();
    }

    init() {
        this.bindEventListeners();
        this.updateProfileLink();
        this.loadUserSelector();
        this.loadCurrentPage();
    }
    
    updateProfileLink() {
        // Update the profile link to point to the current user
        const profileLink = document.getElementById('profileLink');
        if (profileLink) {
            profileLink.href = `/profile/${this.currentUserId}`;
        }
    }

    bindEventListeners() {
        // User selector change
        const userSelector = document.getElementById('userSelector');
        if (userSelector) {
            userSelector.addEventListener('change', (e) => {
                this.currentUserId = parseInt(e.target.value);
                // Save the user ID to localStorage
                localStorage.setItem('currentUserId', this.currentUserId.toString());
                // Update the profile link
                this.updateProfileLink();
                this.handleUserChange();
            });
        }

        // Post form submission
        const postForm = document.getElementById('postForm');
        if (postForm) {
            postForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitPost();
            });
        }

        // Delegate event listeners for dynamic content
        document.addEventListener('click', (e) => {
            // Handle like button clicks, including when icon is clicked
            if (e.target.classList.contains('like-btn') || 
                (e.target.parentElement && e.target.parentElement.classList.contains('like-btn'))) {
                // Get the actual button element
                const button = e.target.classList.contains('like-btn') ? e.target : e.target.parentElement;
                this.handleLike(button);
            } else if (e.target.classList.contains('comment-submit')) {
                this.handleCommentSubmit(e.target);
            }
        });

        // Handle Enter key in comment inputs
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.target.classList.contains('comment-input')) {
                e.preventDefault();
                const submitBtn = e.target.parentNode.querySelector('.comment-submit');
                if (submitBtn) {
                    this.handleCommentSubmit(submitBtn);
                }
            }
        });
    }

    async loadUserSelector() {
        try {
            const response = await fetch('/api/v1/users');
            if (response.ok) {
                const users = await response.json();
                const selector = document.getElementById('userSelector');
                if (selector && users.length > 0) {
                    selector.innerHTML = users.map(user => 
                        `<option value="${user.id}" ${user.id === this.currentUserId ? 'selected' : ''}>
                            ${user.username}
                        </option>`
                    ).join('');
                    
                    // Force the selector to match the current user ID (fixes browser cache issues)
                    selector.value = this.currentUserId;
                }
            }
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }

    loadCurrentPage() {
        const path = window.location.pathname;
        if (path === '/' || path === '/home') {
            this.loadFeed();
        } else if (path.startsWith('/profile/')) {
            const userId = path.split('/')[2];
            this.loadProfile(userId);
        }
    }

    handleUserChange() {
        const path = window.location.pathname;
        if (path === '/' || path === '/home') {
            // On home page, reload the feed for the new user
            this.loadFeed();
        } else if (path.startsWith('/profile/')) {
            // On profile page, navigate to the new user's profile
            window.location.href = `/profile/${this.currentUserId}`;
        } else {
            // For other pages, just reload current page content
            this.loadCurrentPage();
        }
    }

    async loadFeed() {
        const feedContainer = document.getElementById('feedContainer');
        if (!feedContainer) return;

        feedContainer.innerHTML = '<div class="loading">Loading your personalized feed...</div>';

        try {
            const response = await fetch(`/api/v1/feed/${this.currentUserId}`);
            if (response.ok) {
                const posts = await response.json();
                if (posts.length === 0) {
                    feedContainer.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">📝</div>
                            <h3>No posts in your feed</h3>
                            <p>Follow some users or create your first post to see content here.</p>
                        </div>
                    `;
                } else {
                    feedContainer.innerHTML = posts.map(post => this.renderPost(post)).join('');
                    this.loadPostInteractions(posts);
                }
            } else {
                throw new Error('Failed to load feed');
            }
        } catch (error) {
            console.error('Error loading feed:', error);
            feedContainer.innerHTML = '<div class="error">Error loading feed. Please try again.</div>';
        }
    }

    async loadProfile(userId) {
        const profileContainer = document.getElementById('profileContainer');
        if (!profileContainer) return;

        profileContainer.innerHTML = '<div class="loading">Loading profile...</div>';

        try {
            // Load comprehensive profile data using our new endpoint
            const profileResponse = await fetch(`/api/v1/users/${userId}/profile`);
            if (!profileResponse.ok) throw new Error('User not found');
            const profile = await profileResponse.json();
            
            // Load user's detailed posts with comment and like counts
            const postsResponse = await fetch(`/api/v1/users/${userId}/detailed_posts`);
            const posts = postsResponse.ok ? await postsResponse.json() : [];
            
            // Load user's comments
            const commentsResponse = await fetch(`/api/v1/users/${userId}/comments`);
            const comments = commentsResponse.ok ? await commentsResponse.json() : [];
            
            // Load user's likes for the current viewer
            const likesResponse = await fetch(`/api/v1/likes/${userId}`);
            const likes = likesResponse.ok ? await likesResponse.json() : [];
            
            // Top tags directly from profile
            const topTags = profile.top_tags || [];

            // Avatar: use first letter of username or emoji
            const avatar = profile.username ? profile.username[0].toUpperCase() : '👤';
            // Join date: format nicely if available
            let joinDate = profile.created_at ? this.formatDateLong(profile.created_at) : '';

            profileContainer.innerHTML = `
                <div class="profile-header">
                    <div class="profile-avatar">${avatar}</div>
                    <div class="profile-info">
                        <div class="profile-username">${profile.username}</div>
                        <div class="profile-meta">
                            <span>User ID: <b>${profile.id}</b></span>
                            ${joinDate ? `&nbsp;|&nbsp; Joined: <b>${joinDate}</b>` : ''}
                        </div>
                        <div class="profile-stats">
                            <div class="stat"><span class="stat-icon">📝</span> <span class="stat-number">${profile.stats.post_count}</span> Posts</div>
                            <div class="stat"><span class="stat-icon">❤️</span> <span class="stat-number">${profile.stats.like_count}</span> Likes Given</div>
                            <div class="stat"><span class="stat-icon">💬</span> <span class="stat-number">${profile.stats.comment_count}</span> Comments</div>
                            <div class="stat"><span class="stat-icon">🌟</span> <span class="stat-number">${profile.stats.likes_received}</span> Likes Received</div>
                        </div>
                        ${topTags && topTags.length > 0 ? `
                        <div class="profile-tags">
                            <span>Top tags:</span>
                            ${topTags.map(tag => `<span class="tag">#${tag}</span>`).join(' ')}
                        </div>` : ''}
                    </div>
                </div>
                
                <div class="recent-posts-title">Recent Posts</div>
                <ul class="recent-posts-list">
                    ${posts.length > 0 
                        ? posts.slice(0, 5).map(post => `
                            <li class="recent-post">
                                <div class="recent-post-title">${this.escapeHtml(post.title)}</div>
                                <div class="recent-post-content">${this.escapeHtml(post.content || '').slice(0, 120)}${post.content && post.content.length > 120 ? '...' : ''}</div>
                                <div class="recent-post-meta">
                                    ${this.formatDate(post.created_at)} &middot; 
                                    <span class="interaction-count"><span class="icon">❤️</span> ${post.like_count}</span> &middot; 
                                    <span class="interaction-count"><span class="icon">💬</span> ${post.comment_count}</span>
                                    ${post.tags && post.tags.length > 0 ? ' &middot; ' + post.tags.map(tag => `<span class='tag'>#${tag}</span>`).join(' ') : ''}
                                </div>
                            </li>
                        `).join('')
                        : '<div class="empty-state"><h3>No posts yet</h3><p>This user hasn\'t posted anything yet.</p></div>'
                    }
                </ul>
                
                ${comments.length > 0 ? `
                <div class="recent-posts-title">Recent Comments</div>
                <ul class="recent-posts-list">
                    ${comments.map(comment => `
                        <li class="recent-post comment-item">
                            <div class="recent-post-title">On post: ${this.escapeHtml(comment.post_title)}</div>
                            <div class="recent-post-content">${this.escapeHtml(comment.content || '')}</div>
                            <div class="recent-post-meta">${this.formatDate(comment.timestamp)}</div>
                        </li>
                    `).join('')}
                </ul>
                ` : ''}
            `;

            if (posts.length > 0) {
                this.loadPostInteractionsForProfile(posts, userId);
            }
        } catch (error) {
            console.error('Error loading profile:', error);
            profileContainer.innerHTML = '<div class="error">Error loading profile. Please try again.</div>';
        }
    }

    formatDateLong(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
    }

    async loadPostInteractions(posts) {
        // Load likes and comments for each post (for feed page - uses current user)
        for (const post of posts) {
            try {
                // Load likes for this post
                const likesResponse = await fetch(`/api/v1/likes/${this.currentUserId}`);
                if (likesResponse.ok) {
                    const userLikes = await likesResponse.json();
                    const hasLiked = userLikes.some(like => like.post_id === post.id);
                    
                    const likeBtn = document.querySelector(`[data-post-id="${post.id}"] .like-btn`);
                    if (likeBtn) {
                        likeBtn.classList.toggle('liked', hasLiked);
                        likeBtn.innerHTML = `<span class="icon">${hasLiked ? '❤️' : '🤍'}</span> Like`;
                        console.log(`Post ${post.id} like state: ${hasLiked ? 'liked' : 'not liked'}`);
                    } else {
                        console.warn(`Like button not found for post ${post.id}`);
                    }
                }

                // Load comments for this post
                const commentsResponse = await fetch(`/api/v1/comments/${post.id}`);
                if (commentsResponse.ok) {
                    const comments = await commentsResponse.json();
                    const commentsContainer = document.querySelector(`[data-post-id="${post.id}"] .comments-section`);
                    if (commentsContainer) {
                        const commentsHtml = comments.map(comment => `
                            <div class="comment">
                                <div class="comment-author">User ${comment.user_id}</div>
                                <div class="comment-content">${this.escapeHtml(comment.content)}</div>
                            </div>
                        `).join('');
                        
                        commentsContainer.innerHTML = `
                            ${commentsHtml}
                            <div class="comment-form">
                                <textarea class="comment-input form-control" placeholder="Write a comment..." rows="1"></textarea>
                                <button class="comment-submit btn btn-primary btn-small">Post</button>
                            </div>
                        `;
                    }
                }
            } catch (error) {
                console.error(`Error loading interactions for post ${post.id}:`, error);
            }
        }
    }

    async loadPostInteractionsForProfile(posts, profileUserId) {
        // Load likes and comments for each post (for profile page - uses selected user for like states)
        for (const post of posts) {
            try {
                // Load likes for this post using the current selected user (not profile user)
                const likesResponse = await fetch(`/api/v1/likes/${this.currentUserId}`);
                if (likesResponse.ok) {
                    const userLikes = await likesResponse.json();
                    const hasLiked = userLikes.some(like => like.post_id === post.id);
                    
                    const likeBtn = document.querySelector(`[data-post-id="${post.id}"] .like-btn`);
                    if (likeBtn) {
                        likeBtn.classList.toggle('liked', hasLiked);
                        likeBtn.innerHTML = `<span class="icon">${hasLiked ? '❤️' : '🤍'}</span> Like`;
                    }
                }

                // Load comments for this post
                const commentsResponse = await fetch(`/api/v1/comments/${post.id}`);
                if (commentsResponse.ok) {
                    const comments = await commentsResponse.json();
                    const commentsContainer = document.querySelector(`[data-post-id="${post.id}"] .comments-section`);
                    if (commentsContainer) {
                        const commentsHtml = comments.map(comment => `
                            <div class="comment">
                                <div class="comment-author">User ${comment.user_id}</div>
                                <div class="comment-content">${this.escapeHtml(comment.content)}</div>
                            </div>
                        `).join('');
                        
                        commentsContainer.innerHTML = `
                            ${commentsHtml}
                            <div class="comment-form">
                                <textarea class="comment-input form-control" placeholder="Write a comment..." rows="1"></textarea>
                                <button class="comment-submit btn btn-primary btn-small">Post</button>
                            </div>
                        `;
                    }
                }
            } catch (error) {
                console.error(`Error loading interactions for post ${post.id}:`, error);
            }
        }
    }

    renderPost(post) {
        return `
            <div class="post" data-post-id="${post.id}">
                <div class="post-header">
                    <div class="post-author">User ${post.creator_id}</div>
                    <div class="post-time">${this.formatDate(post.created_at)}</div>
                </div>
                <div class="post-title">${this.escapeHtml(post.title)}</div>
                <div class="post-content">${this.escapeHtml(post.content || '')}</div>
                <div class="post-tags">
                    ${post.tags.map(tag => `<span class="tag">#${tag}</span>`).join('')}
                </div>
                <div class="post-actions">
                    <button class="post-action like-btn" data-post-id="${post.id}">
                        <span class="icon">🤍</span> Like
                    </button>
                    <div class="post-action">
                        <span class="icon">💬</span> Comment
                    </div>
                </div>
                <div class="comments-section"></div>
            </div>
        `;
    }

    async handleLike(button) {
        // Get post ID from data attribute (support both camelCase and kebab-case)
        const postId = parseInt(button.dataset.postId || button.dataset.postId || button.getAttribute('data-post-id'));
        if (!postId) {
            console.error('Post ID not found on like button', button);
            return;
        }
        const isLiked = button.classList.contains('liked');

        try {
            const method = isLiked ? 'DELETE' : 'POST';
            const response = await fetch('/api/v1/likes', {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.currentUserId,
                    post_id: postId
                })
            });

            if (response.ok) {
                // Toggle the liked state
                const newIsLiked = !isLiked;
                button.classList.toggle('liked', newIsLiked);
                button.innerHTML = `<span class="icon">${newIsLiked ? '❤️' : '🤍'}</span> Like`;
                
                // Log success for debugging
                console.log(`Successfully ${newIsLiked ? 'liked' : 'unliked'} post ${postId}`);
            } else {
                // Handle error response
                let errorMessage = 'Failed to update like';
                try {
                    const error = await response.json();
                    errorMessage = error.detail || errorMessage;
                } catch (e) {
                    // If response is not JSON
                    errorMessage = `${response.status}: ${response.statusText}`;
                }
                console.error('Like API error:', errorMessage);
                this.showError(errorMessage);
            }
        } catch (error) {
            console.error('Error handling like:', error);
            this.showError('Network error. Please try again.');
        }
    }

    async handleCommentSubmit(button) {
        const commentForm = button.parentNode;
        const commentInput = commentForm.querySelector('.comment-input');
        const content = commentInput.value.trim();
        
        if (!content) return;

        const postElement = button.closest('.post');
        const postId = parseInt(postElement.dataset.postId);

        try {
            const response = await fetch('/api/v1/comments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.currentUserId,
                    post_id: postId,
                    content: content
                })
            });

            if (response.ok) {
                const comment = await response.json();
                
                // Add the new comment to the UI
                const commentsSection = postElement.querySelector('.comments-section');
                const newCommentHtml = `
                    <div class="comment">
                        <div class="comment-author">User ${comment.user_id}</div>
                        <div class="comment-content">${this.escapeHtml(comment.content)}</div>
                    </div>
                `;
                
                commentsSection.insertAdjacentHTML('afterbegin', newCommentHtml);
                commentInput.value = '';
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Failed to post comment');
            }
        } catch (error) {
            console.error('Error posting comment:', error);
            this.showError('Network error. Please try again.');
        }
    }

    async submitPost() {
        const form = document.getElementById('postForm');
        const formData = new FormData(form);
        
        const title = formData.get('title').trim();
        const content = formData.get('content').trim();
        const tagsString = formData.get('tags').trim();
        const tags = tagsString ? tagsString.split(',').map(tag => tag.trim()).filter(tag => tag) : [];

        if (!title) {
            this.showError('Title is required');
            return;
        }

        try {
            const response = await fetch('/api/v1/posts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: title,
                    content: content,
                    creator_id: this.currentUserId,
                    tags: tags
                })
            });

            if (response.ok) {
                this.showSuccess('Post created successfully!');
                form.reset();
                // Redirect to user's profile page after a short delay
                setTimeout(() => {
                    window.location.href = `/profile/${this.currentUserId}`;
                }, 1000);
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Failed to create post');
            }
        } catch (error) {
            console.error('Error creating post:', error);
            this.showError('Network error. Please try again.');
        }
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h`;
        if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d`;
        
        return date.toLocaleDateString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showMessage(message, type) {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.error, .success');
        existingMessages.forEach(msg => msg.remove());

        // Create new message
        const messageDiv = document.createElement('div');
        messageDiv.className = type;
        messageDiv.textContent = message;

        // Insert at the top of the main content
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.insertBefore(messageDiv, mainContent.firstChild);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }
    }
}

// Analytics functionality
class AnalyticsPage {
    constructor() {
        this.init();
    }

    async init() {
        // Check if we're on the analytics page
        if (window.location.pathname !== '/analytics') return;
        
        try {
            // Show loading state
            document.getElementById('loadingSpinner').style.display = 'flex';
            
            // Fetch analytics data
            const response = await fetch('/api/v1/analytics');
            if (!response.ok) {
                throw new Error('Failed to load analytics data');
            }
            
            const data = await response.json();
            
            // Render analytics components
            this.renderTotalCounts(data.total_counts);
            this.renderActiveUsers(data.most_active_users);
            this.renderPopularPosts(data.most_liked_posts);
            this.renderTagCloud(data.top_tags);
            this.renderActivityChart(data.activity_data);
            
            // Hide loading spinner
            document.getElementById('loadingSpinner').style.display = 'none';
        } catch (error) {
            console.error('Error loading analytics:', error);
            document.getElementById('loadingSpinner').textContent = 'Error loading analytics data. Please try again.';
        }
    }
    
    renderTotalCounts(counts) {
        document.getElementById('totalUsers').textContent = this.formatNumber(counts.users);
        document.getElementById('totalPosts').textContent = this.formatNumber(counts.posts);
        document.getElementById('totalComments').textContent = this.formatNumber(counts.comments);
        document.getElementById('totalLikes').textContent = this.formatNumber(counts.likes);
    }
    
    renderActiveUsers(users) {
        const tableBody = document.getElementById('activeUsersTableBody');
        tableBody.innerHTML = users.length > 0 
            ? users.map(user => `
                <tr>
                    <td>
                        <a href="/profile/${user.id}" class="user-link">
                            <span class="user-avatar">${user.username.charAt(0).toUpperCase()}</span>
                            ${user.username}
                        </a>
                    </td>
                    <td>${user.post_count}</td>
                </tr>
            `).join('')
            : '<tr><td colspan="2">No active users found</td></tr>';
    }
    
    renderPopularPosts(posts) {
        const tableBody = document.getElementById('popularPostsTableBody');
        tableBody.innerHTML = posts.length > 0
            ? posts.map(post => `
                <tr>
                    <td>
                        <div class="post-title-cell">${this.escapeHtml(post.title)}</div>
                    </td>
                    <td>${post.like_count}</td>
                </tr>
            `).join('')
            : '<tr><td colspan="2">No liked posts found</td></tr>';
    }
    
    renderTagCloud(tags) {
        const tagCloud = document.getElementById('tagCloud');
        tagCloud.innerHTML = tags.length > 0
            ? tags.map(tag => `
                <div class="analytics-tag">
                    #${tag.name}
                    <span class="tag-count">${tag.count}</span>
                </div>
            `).join('')
            : '<div class="empty-state">No tags found</div>';
    }
    
    renderActivityChart(activityData) {
        const chartBars = document.getElementById('chartBars');
        const chartLabels = document.getElementById('chartLabels');
        
        if (!activityData || activityData.length === 0) {
            chartBars.innerHTML = '<div class="empty-state">No activity data available</div>';
            return;
        }
        
        // Find the maximum count for scaling
        const maxCount = Math.max(...activityData.map(day => day.count));
        
        // Generate the bars
        chartBars.innerHTML = activityData.map(day => {
            const heightPercent = maxCount > 0 ? (day.count / maxCount) * 100 : 0;
            return `
                <div class="chart-bar" style="height: ${heightPercent}%;" title="${day.count} posts on ${day.date}">
                    <span class="bar-value">${day.count}</span>
                </div>
            `;
        }).join('');
        
        // Generate the date labels
        chartLabels.innerHTML = activityData.map(day => {
            // Format the date to show only day and month
            const date = new Date(day.date);
            const formattedDate = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
            return `<div class="chart-label">${formattedDate}</div>`;
        }).join('');
    }
    
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PostFeedApp();
    new AnalyticsPage();
});
