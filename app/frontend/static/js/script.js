// JavaScript for dynamic interactions in the Humdov Post Feed API frontend

class PostFeedApp {
    constructor() {
        this.currentUserId = 1; // Default user
        this.init();
    }

    init() {
        this.bindEventListeners();
        this.loadUserSelector();
        this.loadCurrentPage();
    }

    bindEventListeners() {
        // User selector change
        const userSelector = document.getElementById('userSelector');
        if (userSelector) {
            userSelector.addEventListener('change', (e) => {
                this.currentUserId = parseInt(e.target.value);
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
            if (e.target.classList.contains('like-btn')) {
                this.handleLike(e.target);
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
            // Load user data
            const userResponse = await fetch(`/api/v1/users/${userId}`);
            if (!userResponse.ok) throw new Error('User not found');
            
            const user = await userResponse.json();

            // Load user's posts
            const postsResponse = await fetch(`/api/v1/posts?creator_id=${userId}`);
            const posts = postsResponse.ok ? await postsResponse.json() : [];

            // Load user's likes
            const likesResponse = await fetch(`/api/v1/likes/${userId}`);
            const likes = likesResponse.ok ? await likesResponse.json() : [];

            profileContainer.innerHTML = `
                <div class="profile-header">
                    <div class="profile-info">
                        <div class="profile-username">${user.username}</div>
                        <div class="profile-stats">
                            <div class="stat">
                                <span class="stat-number">${posts.length}</span> Posts
                            </div>
                            <div class="stat">
                                <span class="stat-number">${likes.length}</span> Likes
                            </div>
                        </div>
                    </div>
                </div>
                <div id="userPosts">
                    ${posts.length > 0 
                        ? posts.map(post => this.renderPost(post)).join('')
                        : '<div class="empty-state"><h3>No posts yet</h3><p>This user hasn\'t posted anything yet.</p></div>'
                    }
                </div>
            `;

            if (posts.length > 0) {
                // Use the profile user ID for loading interactions, not this.currentUserId
                this.loadPostInteractionsForProfile(posts, userId);
            }
        } catch (error) {
            console.error('Error loading profile:', error);
            profileContainer.innerHTML = '<div class="error">Error loading profile. Please try again.</div>';
        }
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
        const postId = parseInt(button.dataset.postId);
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
                button.classList.toggle('liked');
                button.innerHTML = `<span class="icon">${isLiked ? '🤍' : '❤️'}</span> Like`;
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Failed to update like');
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
                // Redirect to home page after a short delay
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
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

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PostFeedApp();
});
